#include "Web.h"

#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <WiFi.h>
#include <Update.h>
#include <mbedtls/base64.h>

#include "Fans.h"
#include "Mqtt.h"
#include "Net.h"
#include "NetLog.h"
#include "Power.h"
#include "Settings.h"

extern const uint8_t pageStart[] asm("_binary_web_index_html_gz_start");
extern const uint8_t pageEnd[] asm("_binary_web_index_html_gz_end");
extern const uint8_t logoStart[] asm("_binary_web_logo_svg_start");
extern const uint8_t logoEnd[] asm("_binary_web_logo_svg_end");
extern const uint8_t icon32Start[] asm("_binary_web_icon_32_png_start");
extern const uint8_t icon32End[] asm("_binary_web_icon_32_png_end");
extern const uint8_t icon180Start[] asm("_binary_web_icon_180_png_start");
extern const uint8_t icon180End[] asm("_binary_web_icon_180_png_end");

static AsyncWebServer server(80);
static AsyncEventSource events("/events");

constexpr size_t kMaxBody = 2048;

// ---- auth -------------------------------------------------------------------------------

static uint32_t authFails = 0;
static uint32_t lockUntil = 0;

static bool ctEqual(const char *a, const char *b) {
  size_t la = strlen(a), lb = strlen(b);
  unsigned d = la ^ lb;
  for (size_t i = 0; i < la; i++) d |= (unsigned char)a[i] ^ (unsigned char)b[i % (lb ? lb : 1)];
  return d == 0;
}

enum AuthResult { AUTH_OK, AUTH_LOCKED, AUTH_BAD };

// Basic auth against admin_user / adminPass, including the lockout after repeated failures.
// Sends nothing: callers decide how to answer (the firmware upload must refuse early).
static AuthResult checkAuth(AsyncWebServerRequest *r) {
  if (millis() < lockUntil) return AUTH_LOCKED;
  bool ok = false;
  if (r->hasHeader("Authorization")) {
    const String &h = r->header("Authorization");
    if (h.startsWith("Basic ")) {
      unsigned char dec[160];
      size_t olen = 0;
      String b = h.substring(6);
      if (b.length() < 200 &&
          mbedtls_base64_decode(dec, sizeof dec - 1, &olen, (const unsigned char *)b.c_str(), b.length()) == 0) {
        dec[olen] = 0;
        char expect[100];
        snprintf(expect, sizeof expect, "%s:%s", CFG_ADMIN_USER, settings().adminPass);
        ok = ctEqual((const char *)dec, expect);
      }
    }
  }
  if (ok) {
    authFails = 0;
    return AUTH_OK;
  }
  if (r->hasHeader("Authorization") && ++authFails >= 5) {
    lockUntil = millis() + 30000;
    authFails = 0;
    logf(LOG_WARN, "web: repeated failed logins, locked for 30 s");
  }
  return AUTH_BAD;
}

// Same, and answers the request itself on failure.
static bool authed(AsyncWebServerRequest *r) {
  AuthResult a = checkAuth(r);
  if (a == AUTH_OK) return true;
  if (a == AUTH_LOCKED) {
    r->send(429, "text/plain", "too many attempts, wait a moment");
    return false;
  }
  // 401 without WWW-Authenticate for fetch() would be silent; the header makes the browser ask.
  AsyncWebServerResponse *resp = r->beginResponse(401, "text/plain", "login required");
  resp->addHeader("WWW-Authenticate", "Basic realm=\"fan-remote\"");
  r->send(resp);
  return false;
}

// Browsers send Origin on cross-site POSTs. Refuse any that is not this very host
// (CSRF: a web page elsewhere must not be able to change fans or settings).
static bool sameOrigin(AsyncWebServerRequest *r) {
  if (!r->hasHeader("Origin")) return true;  // curl, scripts, same-origin GET-like fetches
  String o = r->header("Origin");
  int s = o.indexOf("://");
  String host = s >= 0 ? o.substring(s + 3) : o;
  if (host == r->host()) return true;
  r->send(403, "text/plain", "cross-origin request refused");
  return false;
}

// Origin check without answering (the upload callback cannot send).
static bool originOk(AsyncWebServerRequest *r) {
  if (!r->hasHeader("Origin")) return true;
  String o = r->header("Origin");
  int s = o.indexOf("://");
  return (s >= 0 ? o.substring(s + 3) : o) == r->host();
}

static bool controlAllowed(AsyncWebServerRequest *r) {
  if (!sameOrigin(r)) return false;
  return !settings().protectControl || authed(r);
}

// ---- JSON ---------------------------------------------------------------------------------

static String stateJson() {
  JsonDocument d;
  d["id"] = deviceId();
  d["name"] = settings().name;
  d["v"] = FW_VERSION;
  d["up"] = millis() / 1000;
  d["rssi"] = WiFi.RSSI();
  d["mqtt"] = mqttConnected();
  JsonArray pr = d["presets"].to<JsonArray>();
  for (int i = 0; i < kPresets; i++) {
    JsonObject o = pr.add<JsonObject>();
    o["id"] = kPresetIds[i];
    o["speed"] = settings().presets[i];
  }
  JsonArray ch = d["ch"].to<JsonArray>();
  for (int i = 0; i < kFans; i++) {
    FanStatus s = fans.status(i);
    JsonObject o = ch.add<JsonObject>();
    o["n"] = i + 1;
    o["name"] = settings().ch[i].name;
    o["enabled"] = s.enabled;
    o["speed"] = s.speed;
    o["duty"] = serialized(String(s.duty, 1));
    o["rpm"] = s.rpm;
    o["state"] = fancore::stateName(s.state);
    o["fault"] = s.fault;
    o["tach"] = s.tach;
    o["min"] = settings().ch[i].minPct;
    o["max"] = settings().ch[i].maxPct;
  }
  String out;
  serializeJson(d, out);
  return out;
}

static String configJson() {
  const Settings &s = settings();
  JsonDocument d;
  d["name"] = s.name;
  d["rampUp"] = s.rampUp;
  d["rampDown"] = s.rampDown;
  d["bootMode"] = s.bootMode;
  d["protectControl"] = s.protectControl;
  JsonArray pr = d["presets"].to<JsonArray>();
  for (int i = 0; i < kPresets; i++) pr.add(s.presets[i]);
  JsonArray ch = d["ch"].to<JsonArray>();
  for (int i = 0; i < kFans; i++) {
    JsonObject o = ch.add<JsonObject>();
    o["name"] = s.ch[i].name;
    o["enabled"] = s.ch[i].enabled;
    o["min"] = s.ch[i].minPct;
    o["max"] = s.ch[i].maxPct;
    o["tach"] = s.ch[i].tach;
    o["ppr"] = s.ch[i].ppr;
  }
  JsonObject n = d["net"].to<JsonObject>();
  n["mqttHost"] = s.mqttHost;
  n["mqttPort"] = s.mqttPort;
  n["mqttUser"] = s.mqttUser;
  n["mqttPassSet"] = s.mqttPass[0] != 0;   // never send the password back
  n["syslogHost"] = s.syslogHost;
  n["ntpHost"] = s.ntpHost;
  String out;
  serializeJson(d, out);
  return out;
}

static void resJson(JsonArray a, const char *name, const char *host, const ResourceStatus &r) {
  JsonObject o = a.add<JsonObject>();
  o["name"] = name;
  o["host"] = host;
  o["status"] = r.status;
  if (r.lastOkMs) o["lastOkAgoS"] = (millis() - r.lastOkMs) / 1000;
  if (r.lastTryMs) o["lastTryAgoS"] = (millis() - r.lastTryMs) / 1000;
}

// Smallest amount of stack (bytes) a task has ever had left; -1 if the task is not found.
// "async_tcp" runs every web handler (this one included), "loopTask" the network and MQTT code.
static int stackLeft(const char *task) {
  TaskHandle_t h = xTaskGetHandle(task);
  return h ? (int)uxTaskGetStackHighWaterMark(h) : -1;
}

static String netstatusJson() {
  JsonDocument d;
  d["firmware"] = "fan-remote";
  d["version"] = FW_VERSION;
  d["git"] = FW_GIT;
  d["buildDate"] = FW_DATE;
  d["hostname"] = deviceId();
  d["name"] = settings().name;
  d["ip"] = WiFi.localIP().toString();
  d["ssid"] = WiFi.SSID();
  d["rssi"] = WiFi.RSSI();
  d["uptimeS"] = millis() / 1000;
  d["freeHeap"] = ESP.getFreeHeap();
  d["minFreeHeap"] = ESP.getMinFreeHeap();       // lowest since boot
  d["maxAllocHeap"] = ESP.getMaxAllocHeap();     // largest block that can still be allocated
  JsonObject sk = d["stackLeft"].to<JsonObject>();
  sk["async_tcp"] = stackLeft("async_tcp");
  sk["loopTask"] = stackLeft("loopTask");
  sk["fans"] = stackLeft("fans");
  JsonObject pw = d["power"].to<JsonObject>();
  pw["mode"] = powerIdle() ? "standby" : "active";
  pw["cpuMhz"] = powerCpuMhz();
  pw["standbyInS"] = powerIdleInS();
  pw["pwmHz"] = fans.pwmHz(0);
  JsonArray res = d["resources"].to<JsonArray>();
  resJson(res, "mqtt", settings().mqttHost, resMqtt());
  resJson(res, "syslog", settings().syslogHost, resSyslog());
  resJson(res, "ntp", settings().ntpHost, resNtp());
  String out;
  serializeJson(d, out);
  return out;
}

// ---- request helpers -----------------------------------------------------------------------

static void json(AsyncWebServerRequest *r, int code, const String &body) {
  AsyncWebServerResponse *resp = r->beginResponse(code, "application/json", body);
  resp->addHeader("Cache-Control", "no-store");
  r->send(resp);
}

static void err(AsyncWebServerRequest *r, int code, const char *msg) {
  json(r, code, String("{\"error\":\"") + msg + "\"}");
}

static bool numParam(AsyncWebServerRequest *r, const char *name, long lo, long hi, long &out) {
  if (!r->hasParam(name, true)) return false;
  const String &v = r->getParam(name, true)->value();
  if (v.length() == 0 || v.length() > 6) return false;
  char *end;
  long x = strtol(v.c_str(), &end, 10);
  if (*end || x < lo || x > hi) return false;
  out = x;
  return true;
}

static bool strParam(AsyncWebServerRequest *r, const char *name, char *dst, size_t n) {
  if (!r->hasParam(name, true)) return false;
  const String &v = r->getParam(name, true)->value();
  if (v.length() >= n) return false;
  for (size_t i = 0; i < v.length(); i++)
    if ((unsigned char)v[i] < 0x20 || v[i] == 0x7f) return false;  // no control characters
  strcpy(dst, v.c_str());
  return true;
}

static bool hostOk(const char *h) {
  for (; *h; h++)
    if (!(isalnum((unsigned char)*h) || *h == '.' || *h == '-' || *h == '_' || *h == ':')) return false;
  return true;
}

static int channelParam(AsyncWebServerRequest *r, bool &ok) {
  ok = false;
  if (!r->hasParam("ch", true)) return 0;
  const String &v = r->getParam("ch", true)->value();
  if (v == "all") { ok = true; return -1; }
  if (v.length() == 1 && v[0] >= '1' && v[0] <= '0' + kFans) { ok = true; return v[0] - '1'; }
  return 0;
}

// ---- routes ---------------------------------------------------------------------------------

static volatile bool pushNow = false;

static void handleSet(AsyncWebServerRequest *r) {
  powerActivity();
  if (!controlAllowed(r)) return;
  bool ok;
  int ch = channelParam(r, ok);
  if (!ok) return err(r, 400, "ch must be 1..4 or all");
  long sp;
  if (numParam(r, "speed", 0, 100, sp)) {
    fans.setSpeed(ch, sp);
  } else if (r->hasParam("preset", true)) {
    if (!fans.setPreset(ch, r->getParam("preset", true)->value().c_str())) return err(r, 400, "unknown preset");
  } else if (r->hasParam("power", true)) {
    const String &p = r->getParam("power", true)->value();
    if (p == "on") fans.setPower(ch, true);
    else if (p == "off") fans.setPower(ch, false);
    else return err(r, 400, "power must be on or off");
  } else {
    return err(r, 400, "need speed, preset or power");
  }
  pushNow = true;
  json(r, 200, stateJson());
}

static void handleNetconfig(AsyncWebServerRequest *r) {
  powerActivity();
  if (!sameOrigin(r) || !authed(r)) return;
  Settings &s = settings();
  if (r->hasParam("defaults", true)) {
    settingsEraseNet();
    settingsDefaults(true);
  } else {
    char tmp[64];
    long port;
    if (strParam(r, "name", tmp, sizeof s.name)) strcpy(s.name, tmp);
    for (auto &f : {std::pair<const char *, std::pair<char *, size_t>>{"mqttHost", {s.mqttHost, sizeof s.mqttHost}},
                    {"syslogHost", {s.syslogHost, sizeof s.syslogHost}},
                    {"ntpHost", {s.ntpHost, sizeof s.ntpHost}}}) {
      char v[64];
      if (strParam(r, f.first, v, sizeof v)) {
        if (!hostOk(v)) return err(r, 400, "invalid host name");
        strcpy(f.second.first, v);
      }
    }
    if (strParam(r, "mqttUser", tmp, sizeof s.mqttUser)) strcpy(s.mqttUser, tmp);
    if (strParam(r, "mqttPass", tmp, sizeof s.mqttPass)) strcpy(s.mqttPass, tmp);
    if (r->hasParam("mqttPort", true)) {
      if (!numParam(r, "mqttPort", 1, 65535, port)) return err(r, 400, "invalid mqttPort");
      s.mqttPort = port;
    }
    if (strParam(r, "adminPass", tmp, sizeof s.adminPass)) {
      if (strlen(tmp) < 8) return err(r, 400, "admin password needs at least 8 characters");
      strcpy(s.adminPass, tmp);
      netSetOtaPassword(s.adminPass);   // the next upload uses it without a reboot
    }
  }
  settingsSaveNet();
  mqttRefreshDiscovery();   // a new friendly name shows up in Home Assistant at once
  logf(LOG_INFO, "network config changed (applies at next boot)");
  json(r, 200, "{\"ok\":true,\"note\":\"applies at next boot\"}");
}

// POST /api/discovery: resend the Home Assistant discovery; with recreate=1 first remove the
// old entities and announce new ones under a new generation (entity ids follow the names).
static void handleDiscovery(AsyncWebServerRequest *r) {
  powerActivity();
  if (!sameOrigin(r) || !authed(r)) return;
  if (r->hasParam("recreate", true)) {
    Settings &s = settings();
    const int old = s.haGen;
    s.haGen = old >= 250 ? 1 : old + 1;
    settingsSaveAll();
    mqttRecreateDiscovery(old);
    logf(LOG_INFO, "Home Assistant entities: recreate, generation %d -> %d", old, (int)s.haGen);
  } else {
    mqttRefreshDiscovery();
  }
  json(r, 200, "{\"ok\":true}");
}

static void handleConfigGet(AsyncWebServerRequest *r) {
  powerActivity();
  if (!authed(r)) return;
  json(r, 200, configJson());
}

static void handleConfigPost(AsyncWebServerRequest *r) {
  powerActivity();
  if (!sameOrigin(r) || !authed(r)) return;
  char *body = static_cast<char *>(r->_tempObject);
  if (!body) return err(r, 400, "no body");
  JsonDocument d;
  if (deserializeJson(d, body)) return err(r, 400, "invalid JSON");
  Settings &s = settings();

  // Validate everything first, then apply, so a bad request changes nothing.
  Settings n = s;
  auto num = [&](JsonVariantConst v, long lo, long hi, long cur) -> long {
    if (v.isNull()) return cur;
    if (!v.is<long>()) return -1;
    long x = v.as<long>();
    return (x < lo || x > hi) ? -1 : x;
  };
  long x;
  if (!d["name"].isNull()) {
    const char *nm = d["name"] | "";
    if (!*nm || strlen(nm) >= sizeof n.name) return err(r, 400, "bad name");
    strcpy(n.name, nm);
  }
  if ((x = num(d["rampUp"], 1, 100, n.rampUp)) < 0) return err(r, 400, "rampUp 1..100");
  n.rampUp = x;
  if ((x = num(d["rampDown"], 1, 100, n.rampDown)) < 0) return err(r, 400, "rampDown 1..100");
  n.rampDown = x;
  if ((x = num(d["bootMode"], 0, 1, n.bootMode)) < 0) return err(r, 400, "bootMode 0|1");
  n.bootMode = x;
  if (!d["protectControl"].isNull()) {
    if (!d["protectControl"].is<bool>()) return err(r, 400, "protectControl bool");
    n.protectControl = d["protectControl"];
  }
  if (!d["presets"].isNull()) {
    JsonArrayConst a = d["presets"];
    if (a.size() != kPresets) return err(r, 400, "presets needs 5 values");
    for (int i = 0; i < kPresets; i++) {
      if ((x = num(a[i], 0, 100, -1)) < 0) return err(r, 400, "preset 0..100");
      n.presets[i] = x;
    }
  }
  if (!d["ch"].isNull()) {
    JsonArrayConst a = d["ch"];
    if (a.size() != kFans) return err(r, 400, "ch needs 4 entries");
    for (int i = 0; i < kFans; i++) {
      JsonObjectConst c = a[i];
      ChannelCfg &t = n.ch[i];
      if (!c["name"].isNull()) {
        const char *nm = c["name"] | "";
        if (strlen(nm) >= sizeof t.name) return err(r, 400, "bad channel name");   // empty = default label
        strcpy(t.name, nm);
      }
      if (!c["enabled"].isNull()) t.enabled = c["enabled"] | true;
      if (!c["tach"].isNull()) t.tach = c["tach"] | true;
      if ((x = num(c["min"], 0, 90, t.minPct)) < 0) return err(r, 400, "min 0..90");
      t.minPct = x;
      if ((x = num(c["max"], 10, 100, t.maxPct)) < 0) return err(r, 400, "max 10..100");
      t.maxPct = x;
      if ((x = num(c["ppr"], 1, 8, t.ppr)) < 0) return err(r, 400, "ppr 1..8");
      t.ppr = x;
      if (t.maxPct < t.minPct) return err(r, 400, "max must not be below min");
    }
  }
  // Applied. Network fields are deliberately not accepted here (see /api/netconfig).
  strcpy(s.name, n.name);
  s.rampUp = n.rampUp;
  s.rampDown = n.rampDown;
  s.bootMode = n.bootMode;
  s.protectControl = n.protectControl;
  memcpy(s.presets, n.presets, sizeof s.presets);
  for (int i = 0; i < kFans; i++) s.ch[i] = n.ch[i];
  settingsSaveAll();
  settingsSaveNet();
  fans.applyConfig();
  mqttRefreshDiscovery();   // new names / enabled channels reach Home Assistant at once
  pushNow = true;
  logf(LOG_INFO, "settings changed");
  json(r, 200, configJson());
}

// ---- firmware update over HTTP -------------------------------------------------------------
// POST /api/update (multipart, field "firmware", Basic auth). The host makes an outbound
// connection to the board's port 80: no port has to be opened on the host, unlike ArduinoOTA,
// where the board connects back. Refused up front when the login or the origin is wrong; an
// image for another chip fails Update.end() and leaves the running firmware alone.
static AsyncWebServerRequest *upOwner = nullptr;   // request that is allowed to write
static String upError;
static bool upDone = false;   // an image was written AND validated by Update.end()

static void onUpdateBody(AsyncWebServerRequest *r, const String &, size_t index, uint8_t *data, size_t len, bool final) {
  powerActivity();
  if (index == 0) {
    upOwner = nullptr;
    upDone = false;
    upError = "";
    if (checkAuth(r) != AUTH_OK) { upError = "login required"; return; }
    if (!originOk(r)) { upError = "cross-origin request refused"; return; }
    if (Update.isRunning()) Update.abort();   // left over from an upload whose connection died
    if (!Update.begin(UPDATE_SIZE_UNKNOWN, U_FLASH)) { upError = Update.errorString(); return; }
    upOwner = r;
    // A dropped connection never reaches onUpdateDone: free the updater here, or every retry
    // would fail until the next reboot.
    r->onDisconnect([r]() {
      if (upOwner == r) {
        Update.abort();
        upOwner = nullptr;
        logf(LOG_WARN, "firmware update: connection lost, aborted");
      }
    });
    logf(LOG_WARN, "firmware update started");
  }
  if (upOwner != r) return;   // refused, or another upload owns the flash
  if (Update.write(data, len) != len) {
    upError = Update.errorString();
    Update.abort();
    upOwner = nullptr;
    return;
  }
  if (final) {
    if (!Update.end(true)) upError = Update.errorString();   // validates the image, incl. the chip
    else upDone = true;
    upOwner = nullptr;
  }
}

static void onUpdateDone(AsyncWebServerRequest *r) {
  // State of this request only: copy it out and reset, so the next request starts clean even
  // if it carries no file part (then the upload callback never runs at all).
  const bool done = upDone;
  String error = upError;
  upDone = false;
  upError = "";
  if (done && error.length() == 0) {   // never from a request that carried no image
    AsyncWebServerResponse *resp = r->beginResponse(200, "application/json", "{\"ok\":true,\"note\":\"rebooting\"}");
    resp->addHeader("Connection", "close");
    r->send(resp);
    logf(LOG_WARN, "firmware update done, rebooting");
    r->onDisconnect([]() { delay(200); ESP.restart(); });
    return;
  }
  if (upOwner == r) { Update.abort(); upOwner = nullptr; }
  int code = error == "login required" ? 401 : (error.startsWith("cross") ? 403 : 500);
  if (error.length() == 0) error = "no firmware received";
  AsyncWebServerResponse *resp = r->beginResponse(code, "application/json", String("{\"error\":\"") + error + "\"}");
  if (code == 401) resp->addHeader("WWW-Authenticate", "Basic realm=\"fan-remote\"");
  r->send(resp);
  logf(LOG_WARN, "firmware update refused: %s", error.c_str());
}

// Collects a small request body into a malloc'd buffer that the request frees itself.
static void collectBody(AsyncWebServerRequest *r, uint8_t *data, size_t len, size_t index, size_t total) {
  if (total == 0 || total > kMaxBody) return;
  if (index == 0) {
    r->_tempObject = malloc(total + 1);
    if (!r->_tempObject) return;
  }
  if (!r->_tempObject) return;
  memcpy(static_cast<uint8_t *>(r->_tempObject) + index, data, len);
  if (index + len == total) static_cast<char *>(r->_tempObject)[total] = 0;
}

static void sendEmbedded(AsyncWebServerRequest *r, const char *type, const uint8_t *start,
                         const uint8_t *end, bool gz, const char *cache) {
  AsyncWebServerResponse *resp = r->beginResponse(200, type, start, end - start);
  if (gz) resp->addHeader("Content-Encoding", "gzip");
  resp->addHeader("Cache-Control", cache);
  r->send(resp);
}

void webBegin() {
  DefaultHeaders::Instance().addHeader("X-Content-Type-Options", "nosniff");
  DefaultHeaders::Instance().addHeader("X-Frame-Options", "DENY");
  DefaultHeaders::Instance().addHeader("Referrer-Policy", "no-referrer");
  DefaultHeaders::Instance().addHeader(
      "Content-Security-Policy",
      "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
      "img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'");

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *r) {
    powerActivity();
    sendEmbedded(r, "text/html", pageStart, pageEnd, true, "no-cache");
  });
  server.on("/logo.svg", HTTP_GET, [](AsyncWebServerRequest *r) {
    sendEmbedded(r, "image/svg+xml", logoStart, logoEnd, false, "max-age=86400");
  });
  // Browsers that ignore SVG icons (Safari, older ones) ask for /favicon.ico and the touch icon:
  // serve real PNGs. The content type decides, not the extension.
  server.on("/favicon.ico", HTTP_GET, [](AsyncWebServerRequest *r) {
    sendEmbedded(r, "image/png", icon32Start, icon32End, false, "max-age=86400");
  });
  server.on("/apple-touch-icon.png", HTTP_GET, [](AsyncWebServerRequest *r) {
    sendEmbedded(r, "image/png", icon180Start, icon180End, false, "max-age=86400");
  });

  // The page calls this when a finger touches it, so the radio is awake for the real command.
  server.on("/api/wake", HTTP_GET, [](AsyncWebServerRequest *r) {
    powerActivity();
    r->send(204);
  });
  server.on("/api/state", HTTP_GET, [](AsyncWebServerRequest *r) { json(r, 200, stateJson()); });
  server.on("/api/set", HTTP_POST, handleSet);
  server.on("/api/netstatus", HTTP_GET, [](AsyncWebServerRequest *r) { json(r, 200, netstatusJson()); });
  server.on("/api/netconfig", HTTP_POST, handleNetconfig);
  server.on("/api/discovery", HTTP_POST, handleDiscovery);
  server.on("/api/config", HTTP_GET, handleConfigGet);
  // JSON body: the body handler must sit on the route itself (AsyncWebServer::onRequestBody only
  // serves URLs without a route, which is why the first version never received the body).
  server.on("/api/config", HTTP_POST, handleConfigPost, nullptr, collectBody);
  server.on("/api/update", HTTP_POST, onUpdateDone, onUpdateBody);
  server.on("/api/reboot", HTTP_POST, [](AsyncWebServerRequest *r) {
    if (!sameOrigin(r) || !authed(r)) return;
    json(r, 200, "{\"ok\":true}");
    logf(LOG_WARN, "reboot requested");
    r->onDisconnect([]() { ESP.restart(); });
  });
  server.on("/api/wifireset", HTTP_POST, [](AsyncWebServerRequest *r) {
    if (!sameOrigin(r) || !authed(r)) return;
    json(r, 200, "{\"ok\":true}");
    r->onDisconnect([]() { netForgetWifi(); });
  });


  events.onConnect([](AsyncEventSourceClient *c) {
    powerActivity(); c->send(stateJson().c_str(), "state", millis(), 2000); });
  server.addHandler(&events);

  server.onNotFound([](AsyncWebServerRequest *r) { r->send(404, "text/plain", "not found"); });
  server.begin();
}

void webLoop() {
  static uint32_t last = 0, seen = 0;
  uint32_t rev = fans.revision();
  uint32_t now = millis();
  if (events.count() == 0) { seen = rev; pushNow = false; return; }
  if ((pushNow || rev != seen || now - last >= 1000) && now - last >= 100) {
    last = now;
    seen = rev;
    pushNow = false;
    events.send(stateJson().c_str(), "state", now);
  }
}
