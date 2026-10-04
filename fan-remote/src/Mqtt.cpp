#include "Mqtt.h"

#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "Fans.h"
#include "Net.h"
#include "NetLog.h"
#include "Power.h"
#include "Settings.h"

static WiFiClient net;
static PubSubClient mq(net);

static char base[56];       // <prefix>/<id>
static uint32_t lastTry = 0;
static uint32_t retryMs = 2000;
static uint32_t lastInfo = 0;
static uint32_t seenRev = 0;

struct Published {
  int speed = -1;
  int preset = -2;
  int fault = -1;
  int rpm = -1000;
  uint32_t rpmAt = 0;
};
static Published pub[kFans];

static void topic(char *out, size_t n, const char *fmt, ...) __attribute__((format(printf, 3, 4)));
static void topic(char *out, size_t n, const char *fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(out, n, fmt, ap);
  va_end(ap);
}

static bool put(const char *t, const char *payload, bool retain) {
  return mq.publish(t, payload, retain);
}

// ---- state ------------------------------------------------------------------------

static void publishChannel(int i, bool force) {
  FanStatus s = fans.status(i);
  Published &p = pub[i];
  char t[96], v[16];

  if (force || p.speed != s.speed) {
    topic(t, sizeof t, "%s/%d/speed/state", base, i + 1);
    snprintf(v, sizeof v, "%d", s.speed);
    put(t, v, true);
    topic(t, sizeof t, "%s/%d/power/state", base, i + 1);
    put(t, s.speed ? "ON" : "OFF", true);
    p.speed = s.speed;
  }
  int pre = s.speed ? Fans::presetFor(s.speed) : -1;
  if (force || p.preset != pre) {
    topic(t, sizeof t, "%s/%d/preset/state", base, i + 1);
    put(t, pre >= 0 ? kPresetIds[pre] : "None", true);
    p.preset = pre;
  }
  if (force || p.fault != (int)s.fault) {
    topic(t, sizeof t, "%s/%d/fault", base, i + 1);
    put(t, s.fault ? "ON" : "OFF", true);
    p.fault = s.fault;
  }
  if (force || abs((int)s.rpm - p.rpm) >= 10 || millis() - p.rpmAt > 30000) {
    topic(t, sizeof t, "%s/%d/rpm", base, i + 1);
    snprintf(v, sizeof v, "%u", s.rpm);
    put(t, v, false);
    p.rpm = s.rpm;
    p.rpmAt = millis();
  }
}

static void publishInfo() {
  char t[64], buf[200];
  topic(t, sizeof t, "%s/info", base);
  snprintf(buf, sizeof buf, "{\"version\":\"%s\",\"ip\":\"%s\",\"rssi\":%d,\"uptime\":%lu}", FW_VERSION,
           WiFi.localIP().toString().c_str(), WiFi.RSSI(), (unsigned long)(millis() / 1000));
  put(t, buf, true);
  lastInfo = millis();
}

// ---- Home Assistant discovery -------------------------------------------------------

// Channel label for Home Assistant: the name set in the settings, else "Fan N".
static const char *label(int i, char *buf, size_t n) {
  const char *nm = settings().ch[i].name;
  if (*nm) return nm;
  snprintf(buf, n, "Fan %d", i + 1);
  return buf;
}

static void addDevice(JsonDocument &d) {
  JsonObject dev = d["device"].to<JsonObject>();
  dev["identifiers"][0] = deviceId();
  dev["name"] = settings().name;
  dev["model"] = "4-channel fan controller";
  dev["manufacturer"] = "DIY";
  dev["sw_version"] = FW_VERSION;
  char url[40];
  snprintf(url, sizeof url, "http://%s.local/", deviceId());
  dev["configuration_url"] = url;
}

static void send(const char *ha, const char *comp, const char *objId, JsonDocument *d) {
  char t[96];
  topic(t, sizeof t, "%s/%s/%s/config", ha, comp, objId);
  if (!d) {  // remove
    mq.publish(t, "", true);
    return;
  }
  String out;
  serializeJson(*d, out);
  if (!mq.beginPublish(t, out.length(), true)) return;
  mq.write((const uint8_t *)out.c_str(), out.length());
  mq.endPublish();
}

static void discovery() {
  const char *ha = CFG_HA_PREFIX;
  const char *id = deviceId();
  char status[64], obj[48], uid[48], tp[96];
  topic(status, sizeof status, "%s/status", base);

  for (int i = 0; i < kFans; i++) {
    const int n = i + 1;
    const ChannelCfg &c = settings().ch[i];
    char lbl[24];
    const char *cname = label(i, lbl, sizeof lbl);
    char objFan[40], objNum[40], objRpm[40], objFault[40];
    topic(objNum, sizeof objNum, "%s_%d_speed", id, n);
    topic(objFan, sizeof objFan, "%s_%d", id, n);
    topic(objRpm, sizeof objRpm, "%s_%d_rpm", id, n);
    topic(objFault, sizeof objFault, "%s_%d_fault", id, n);
    if (!c.enabled) {
      send(ha, "fan", objFan, nullptr);
      send(ha, "number", objNum, nullptr);
      send(ha, "sensor", objRpm, nullptr);
      send(ha, "binary_sensor", objFault, nullptr);
      continue;
    }

    {
      JsonDocument d;
      d["name"] = cname;
      d["unique_id"] = objFan;
      d["availability_topic"] = status;
      d["icon"] = "mdi:fan";
      topic(tp, sizeof tp, "%s/%d/power/set", base, n);
      d["command_topic"] = tp;
      topic(tp, sizeof tp, "%s/%d/power/state", base, n);
      d["state_topic"] = tp;
      topic(tp, sizeof tp, "%s/%d/speed/set", base, n);
      d["percentage_command_topic"] = tp;
      topic(tp, sizeof tp, "%s/%d/speed/state", base, n);
      d["percentage_state_topic"] = tp;
      d["speed_range_min"] = 1;
      d["speed_range_max"] = 100;
      topic(tp, sizeof tp, "%s/%d/preset/set", base, n);
      d["preset_mode_command_topic"] = tp;
      topic(tp, sizeof tp, "%s/%d/preset/state", base, n);
      d["preset_mode_state_topic"] = tp;
      JsonArray modes = d["preset_modes"].to<JsonArray>();
      for (int k = 0; k < kPresets; k++) modes.add(kPresetIds[k]);
      addDevice(d);
      send(ha, "fan", objFan, &d);
    }
    {
      // A plain 0..100 % slider on the device page and in every default dashboard (the fan
      // entity's own speed control hides behind its more-info dialog).
      JsonDocument d;
      snprintf(uid, sizeof uid, "%s %s", cname, "speed");
      d["name"] = uid;
      d["unique_id"] = objNum;
      d["availability_topic"] = status;
      topic(tp, sizeof tp, "%s/%d/speed/set", base, n);
      d["command_topic"] = tp;
      topic(tp, sizeof tp, "%s/%d/speed/state", base, n);
      d["state_topic"] = tp;
      d["min"] = 0;
      d["max"] = 100;
      d["step"] = 1;
      d["mode"] = "slider";
      d["unit_of_measurement"] = "%";
      d["icon"] = "mdi:fan-speed-3";
      addDevice(d);
      send(ha, "number", objNum, &d);
    }
    if (c.tach) {
      JsonDocument d;
      snprintf(uid, sizeof uid, "%s %s", cname, "RPM");
      d["name"] = uid;
      d["unique_id"] = objRpm;
      d["availability_topic"] = status;
      topic(tp, sizeof tp, "%s/%d/rpm", base, n);
      d["state_topic"] = tp;
      d["unit_of_measurement"] = "rpm";
      d["state_class"] = "measurement";
      d["icon"] = "mdi:fan";
      d["suggested_display_precision"] = 0;
      addDevice(d);
      send(ha, "sensor", objRpm, &d);

      JsonDocument f;
      snprintf(uid, sizeof uid, "%s %s", cname, "stalled");
      f["name"] = uid;
      f["unique_id"] = objFault;
      f["availability_topic"] = status;
      topic(tp, sizeof tp, "%s/%d/fault", base, n);
      f["state_topic"] = tp;
      f["device_class"] = "problem";
      f["payload_on"] = "ON";
      f["payload_off"] = "OFF";
      addDevice(f);
      send(ha, "binary_sensor", objFault, &f);
    } else {
      send(ha, "sensor", objRpm, nullptr);
      send(ha, "binary_sensor", objFault, nullptr);
    }
  }

  char info[64];
  topic(info, sizeof info, "%s/info", base);
  struct Diag { const char *key, *name, *cls, *unit, *tmpl; };
  const Diag diags[] = {
      {"rssi", "WiFi signal", "signal_strength", "dBm", "{{ value_json.rssi }}"},
      {"uptime", "Uptime", "duration", "s", "{{ value_json.uptime }}"},
  };
  for (const Diag &g : diags) {
    JsonDocument d;
    d["name"] = g.name;
    topic(obj, sizeof obj, "%s_%s", id, g.key);
    d["unique_id"] = obj;
    d["availability_topic"] = status;
    d["state_topic"] = info;
    d["value_template"] = g.tmpl;
    d["device_class"] = g.cls;
    d["unit_of_measurement"] = g.unit;
    d["entity_category"] = "diagnostic";
    d["state_class"] = "measurement";
    addDevice(d);
    send(ha, "sensor", obj, &d);
  }
}

// ---- commands ---------------------------------------------------------------------------

// Parse a plain decimal 0..100; false for anything else.
static bool parseSpeed(const uint8_t *p, unsigned len, int &out) {
  if (len == 0 || len > 3) return false;
  int v = 0;
  for (unsigned i = 0; i < len; i++) {
    if (p[i] < '0' || p[i] > '9') return false;
    v = v * 10 + (p[i] - '0');
  }
  if (v > 100) return false;
  out = v;
  return true;
}

static void onMessage(char *tpc, uint8_t *payload, unsigned len) {
  // <base>/<ch|all>/<speed|power|preset>/set
  size_t bl = strlen(base);
  if (strncmp(tpc, base, bl) != 0 || tpc[bl] != '/') return;
  char rest[40];
  strncpy(rest, tpc + bl + 1, sizeof rest - 1);
  rest[sizeof rest - 1] = 0;
  char *chs = strtok(rest, "/");
  char *what = strtok(nullptr, "/");
  char *set = strtok(nullptr, "/");
  if (!chs || !what || !set || strcmp(set, "set") != 0) return;

  int ch;
  if (strcmp(chs, "all") == 0) ch = -1;
  else if (strlen(chs) == 1 && chs[0] >= '1' && chs[0] <= '0' + kFans) ch = chs[0] - '1';
  else return;

  char val[24];
  unsigned n = len < sizeof val - 1 ? len : sizeof val - 1;
  memcpy(val, payload, n);
  val[n] = 0;

  if (strcmp(what, "speed") == 0) {
    int s;
    if (!parseSpeed(payload, len, s)) { logf(LOG_WARN, "mqtt: bad speed payload on %s", tpc); return; }
    fans.setSpeed(ch, s);
  } else if (strcmp(what, "power") == 0) {
    if (strcasecmp(val, "ON") == 0) fans.setPower(ch, true);
    else if (strcasecmp(val, "OFF") == 0) fans.setPower(ch, false);
    else return;
  } else if (strcmp(what, "preset") == 0) {
    if (!fans.setPreset(ch, val)) { logf(LOG_WARN, "mqtt: unknown preset on %s", tpc); return; }
  } else {
    return;
  }
  powerActivity();
  seenRev = 0;  // publish the new state right away
}

// ---- connection ----------------------------------------------------------------------------

static bool connect() {
  Settings &s = settings();
  if (!s.mqttHost[0]) return false;
  mq.setServer(s.mqttHost, s.mqttPort);  // the name is resolved on every connect
  char lwt[64];
  topic(lwt, sizeof lwt, "%s/status", base);
  bool ok = s.mqttUser[0] ? mq.connect(deviceId(), s.mqttUser, s.mqttPass, lwt, 0, true, "offline")
                          : mq.connect(deviceId(), nullptr, nullptr, lwt, 0, true, "offline");
  char st[48];
  if (ok) snprintf(st, sizeof st, "connected");
  else snprintf(st, sizeof st, "rc=%d", mq.state());
  resSet(resMqtt(), ok, st);
  return ok;
}

void mqttBegin() {
  snprintf(base, sizeof base, "%s/%s", CFG_MQTT_PREFIX, deviceId());
  mq.setBufferSize(1536);
  mq.setKeepAlive(30);
  mq.setSocketTimeout(3);
  mq.setCallback(onMessage);
  if (!settings().mqttHost[0]) resSet(resMqtt(), false, "unused");
}

bool mqttConnected() { return mq.connected(); }

void mqttLoop() {
  if (!netConnected() || !settings().mqttHost[0]) return;

  if (!mq.connected()) {
    if (millis() - lastTry < retryMs) return;
    lastTry = millis();
    if (!connect()) {
      retryMs = retryMs < 60000 ? retryMs * 2 : 60000;  // back off to once a minute
      logf(LOG_WARN, "mqtt connect to %s failed: %s", settings().mqttHost, resMqtt().status);
      return;
    }
    retryMs = 2000;
    logf(LOG_INFO, "mqtt connected to %s", settings().mqttHost);
    char t[96];
    topic(t, sizeof t, "%s/status", base);
    put(t, "online", true);
    for (const char *w : {"speed", "power", "preset"}) {
      topic(t, sizeof t, "%s/+/%s/set", base, w);
      mq.subscribe(t);
    }
    discovery();
    for (int i = 0; i < kFans; i++) publishChannel(i, true);
    publishInfo();
    seenRev = fans.revision();
  }

  mq.loop();

  uint32_t r = fans.revision();
  static uint32_t lastPub = 0;
  if ((r != seenRev || millis() - lastPub > 1000) && millis() - lastPub > 150) {
    seenRev = r;
    lastPub = millis();
    for (int i = 0; i < kFans; i++)
      if (settings().ch[i].enabled) publishChannel(i, false);
  }
  if (millis() - lastInfo > 60000) publishInfo();
}
