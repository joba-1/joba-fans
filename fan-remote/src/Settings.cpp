#include "Settings.h"

#include <Preferences.h>
#include <esp_mac.h>

const char *const kPresetIds[kPresets] = {"quiet", "low", "medium", "high", "max"};

static Settings g;
static const char *NS = "fan";

Settings &settings() { return g; }

const char *deviceId() {
  static char id[16];
  if (!id[0]) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    snprintf(id, sizeof id, "fan-%02x%02x%02x", mac[3], mac[4], mac[5]);
  }
  return id;
}

static void cpy(char *dst, size_t n, const String &s) {
  strncpy(dst, s.c_str(), n - 1);
  dst[n - 1] = 0;
}

void settingsDefaults(bool netOnly) {
  cpy(g.mqttHost, sizeof g.mqttHost, CFG_MQTT_HOST);
  g.mqttPort = CFG_MQTT_PORT;
  cpy(g.mqttUser, sizeof g.mqttUser, CFG_MQTT_USER);
  cpy(g.mqttPass, sizeof g.mqttPass, CFG_MQTT_PASSWORD);
  cpy(g.syslogHost, sizeof g.syslogHost, CFG_SYSLOG_HOST);
  cpy(g.ntpHost, sizeof g.ntpHost, CFG_NTP_HOST);
  if (netOnly) return;

  cpy(g.name, sizeof g.name, String("Fans ") + (deviceId() + 4));
  cpy(g.adminPass, sizeof g.adminPass, CFG_ADMIN_PASSWORD);
  for (int i = 0; i < kFans; i++) {
    snprintf(g.ch[i].name, sizeof g.ch[i].name, "Fan %d", i + 1);
    g.ch[i].enabled = true;
    g.ch[i].minPct = 20;
    g.ch[i].maxPct = 100;
    g.ch[i].tach = true;
    g.ch[i].ppr = 2;
    g.lastSpeed[i] = 0;
    g.lastOn[i] = 40;
  }
  const uint8_t p[kPresets] = {10, 30, 50, 75, 100};
  memcpy(g.presets, p, sizeof p);
  g.rampUp = 10;
  g.rampDown = 20;
  g.bootMode = 0;
  g.protectControl = false;
}

void settingsLoad() {
  settingsDefaults(false);
  Preferences p;
  if (!p.begin(NS, true)) return;
  auto str = [&](const char *key, char *dst, size_t n) {
    if (p.isKey(key)) cpy(dst, n, p.getString(key));
  };
  str("name", g.name, sizeof g.name);
  str("adminPass", g.adminPass, sizeof g.adminPass);
  str("mqttHost", g.mqttHost, sizeof g.mqttHost);
  g.mqttPort = p.getUShort("mqttPort", g.mqttPort);
  str("mqttUser", g.mqttUser, sizeof g.mqttUser);
  str("mqttPass", g.mqttPass, sizeof g.mqttPass);
  str("syslogHost", g.syslogHost, sizeof g.syslogHost);
  str("ntpHost", g.ntpHost, sizeof g.ntpHost);
  g.rampUp = p.getUChar("rampUp", g.rampUp);
  g.rampDown = p.getUChar("rampDown", g.rampDown);
  g.bootMode = p.getUChar("bootMode", g.bootMode);
  g.protectControl = p.getBool("protect", g.protectControl);
  for (int i = 0; i < kPresets; i++) {
    char k[8];
    snprintf(k, sizeof k, "pre%d", i);
    g.presets[i] = p.getUChar(k, g.presets[i]);
  }
  for (int i = 0; i < kFans; i++) {
    char k[12];
    snprintf(k, sizeof k, "c%dname", i);
    str(k, g.ch[i].name, sizeof g.ch[i].name);
    snprintf(k, sizeof k, "c%den", i);
    g.ch[i].enabled = p.getBool(k, g.ch[i].enabled);
    snprintf(k, sizeof k, "c%dmin", i);
    g.ch[i].minPct = p.getUChar(k, g.ch[i].minPct);
    snprintf(k, sizeof k, "c%dmax", i);
    g.ch[i].maxPct = p.getUChar(k, g.ch[i].maxPct);
    snprintf(k, sizeof k, "c%dtach", i);
    g.ch[i].tach = p.getBool(k, g.ch[i].tach);
    snprintf(k, sizeof k, "c%dppr", i);
    g.ch[i].ppr = p.getUChar(k, g.ch[i].ppr);
    snprintf(k, sizeof k, "c%dlast", i);
    g.lastSpeed[i] = p.getUChar(k, g.lastSpeed[i]);
    snprintf(k, sizeof k, "c%don", i);
    g.lastOn[i] = p.getUChar(k, g.lastOn[i]);
  }
  p.end();

  // Whatever is in flash, keep the values inside what the firmware can handle.
  for (int i = 0; i < kFans; i++) {
    ChannelCfg &c = g.ch[i];
    if (c.minPct > 90) c.minPct = 90;
    if (c.maxPct > 100) c.maxPct = 100;
    if (c.maxPct < c.minPct) c.maxPct = c.minPct;
    if (c.ppr < 1 || c.ppr > 8) c.ppr = 2;
    if (g.lastSpeed[i] > 100) g.lastSpeed[i] = 0;
    if (g.lastOn[i] < 1 || g.lastOn[i] > 100) g.lastOn[i] = 40;
  }
  for (int i = 0; i < kPresets; i++)
    if (g.presets[i] > 100) g.presets[i] = 100;
}

void settingsSaveNet() {
  Preferences p;
  if (!p.begin(NS, false)) return;
  p.putString("name", g.name);
  p.putString("adminPass", g.adminPass);
  p.putString("mqttHost", g.mqttHost);
  p.putUShort("mqttPort", g.mqttPort);
  p.putString("mqttUser", g.mqttUser);
  p.putString("mqttPass", g.mqttPass);
  p.putString("syslogHost", g.syslogHost);
  p.putString("ntpHost", g.ntpHost);
  p.end();
}

void settingsEraseNet() {
  Preferences p;
  if (!p.begin(NS, false)) return;
  for (const char *k : {"mqttHost", "mqttPort", "mqttUser", "mqttPass", "syslogHost", "ntpHost"})
    p.remove(k);
  p.end();
}

void settingsSaveAll() {
  Preferences p;
  if (!p.begin(NS, false)) return;
  p.putUChar("rampUp", g.rampUp);
  p.putUChar("rampDown", g.rampDown);
  p.putUChar("bootMode", g.bootMode);
  p.putBool("protect", g.protectControl);
  for (int i = 0; i < kPresets; i++) {
    char k[8];
    snprintf(k, sizeof k, "pre%d", i);
    p.putUChar(k, g.presets[i]);
  }
  for (int i = 0; i < kFans; i++) {
    char k[12];
    snprintf(k, sizeof k, "c%dname", i);
    p.putString(k, g.ch[i].name);
    snprintf(k, sizeof k, "c%den", i);
    p.putBool(k, g.ch[i].enabled);
    snprintf(k, sizeof k, "c%dmin", i);
    p.putUChar(k, g.ch[i].minPct);
    snprintf(k, sizeof k, "c%dmax", i);
    p.putUChar(k, g.ch[i].maxPct);
    snprintf(k, sizeof k, "c%dtach", i);
    p.putBool(k, g.ch[i].tach);
    snprintf(k, sizeof k, "c%dppr", i);
    p.putUChar(k, g.ch[i].ppr);
  }
  p.end();
}

void settingsSaveSpeeds() {
  Preferences p;
  if (!p.begin(NS, false)) return;
  for (int i = 0; i < kFans; i++) {
    char k[12];
    snprintf(k, sizeof k, "c%dlast", i);
    p.putUChar(k, g.lastSpeed[i]);
    snprintf(k, sizeof k, "c%don", i);
    p.putUChar(k, g.lastOn[i]);
  }
  p.end();
}
