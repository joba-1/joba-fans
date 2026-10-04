#include "Settings.h"

#include <Preferences.h>
#include <esp_mac.h>

#include "DeviceTable.h"   // generated from devices.csv

const char *const kPresetIds[kPresets] = {"quiet", "low", "medium", "high", "max"};

static Settings g;
static const char *NS = "fan";

Settings &settings() { return g; }

static int deviceNo() {
  static int n = -1;
  if (n < 0) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    n = fancore::deviceNumber(kDeviceTable, kDeviceTableLen, mac);
  }
  return n;
}

bool deviceRegistered() { return deviceNo() > 0; }

// "fan-control-3" from devices.csv; "fan-control-new-xxxxxx" for a board that is not registered yet.
const char *deviceId() {
  static char id[24];
  if (!id[0]) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    fancore::formatDeviceId(id, sizeof id, deviceNo(), mac);
  }
  return id;
}

static void cpy(char *dst, size_t n, const String &s) {
  strncpy(dst, s.c_str(), n - 1);
  dst[n - 1] = 0;
}

static void fillDefaults(Settings &s, bool netOnly) {
  cpy(s.mqttHost, sizeof s.mqttHost, CFG_MQTT_HOST);
  s.mqttPort = CFG_MQTT_PORT;
  cpy(s.mqttUser, sizeof s.mqttUser, CFG_MQTT_USER);
  cpy(s.mqttPass, sizeof s.mqttPass, CFG_MQTT_PASSWORD);
  cpy(s.syslogHost, sizeof s.syslogHost, CFG_SYSLOG_HOST);
  cpy(s.ntpHost, sizeof s.ntpHost, CFG_NTP_HOST);
  if (netOnly) return;

  cpy(s.name, sizeof s.name, deviceId());   // friendly name starts out as the id
  cpy(s.adminPass, sizeof s.adminPass, CFG_ADMIN_PASSWORD);
  for (int i = 0; i < kFans; i++) {
    s.ch[i].name[0] = 0;   // empty = default label, "Fan N" or "Lüfter N" by language
    s.ch[i].enabled = true;
    s.ch[i].minPct = 5;    // lowest duty a fan is asked to keep turning at; raise it for fans that stall
    s.ch[i].maxPct = 100;
    s.ch[i].tach = true;
    s.ch[i].ppr = 2;
    s.lastSpeed[i] = 0;
    s.lastOn[i] = 40;
  }
  const uint8_t p[kPresets] = {10, 30, 50, 75, 100};
  memcpy(s.presets, p, sizeof p);
  s.rampUp = 10;
  s.rampDown = 20;
  s.bootMode = 0;
  s.protectControl = false;
  s.haGen = 0;
}

void settingsDefaults(bool netOnly) { fillDefaults(g, netOnly); }

void settingsLoad() {
  settingsDefaults(false);
  Preferences p;
  // Read-only open fails on a fresh board (namespace not created yet): open read-write once.
  if (!p.begin(NS, false)) return;
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
  g.haGen = p.getUChar("hagen", 0);
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
    char dflt[12];
    snprintf(dflt, sizeof dflt, "Fan %d", i + 1);
    if (strcmp(c.name, dflt) == 0) c.name[0] = 0;   // older firmware stored the default
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

// Only values that differ from the config.ini defaults are stored. A value left at its
// default stays unpinned, so a changed config.ini (a moved alias, a new password) reaches
// every board that never overrode it.
void settingsSaveNet() {
  Settings d;
  fillDefaults(d, false);
  Preferences p;
  if (!p.begin(NS, false)) return;
  auto keep = [&](const char *key, const char *val, const char *def) {
    if (strcmp(val, def) == 0) p.remove(key);
    else p.putString(key, val);
  };
  keep("name", g.name, d.name);
  keep("adminPass", g.adminPass, d.adminPass);
  keep("mqttHost", g.mqttHost, d.mqttHost);
  keep("mqttUser", g.mqttUser, d.mqttUser);
  keep("mqttPass", g.mqttPass, d.mqttPass);
  keep("syslogHost", g.syslogHost, d.syslogHost);
  keep("ntpHost", g.ntpHost, d.ntpHost);
  if (g.mqttPort == d.mqttPort) p.remove("mqttPort");
  else p.putUShort("mqttPort", g.mqttPort);
  p.end();
}

void settingsEraseNet() {
  Preferences p;
  if (!p.begin(NS, false)) return;
  for (const char *k : {"mqttHost", "mqttPort", "mqttUser", "mqttPass", "syslogHost", "ntpHost"})
    p.remove(k);
  p.end();
}

// Like settingsSaveNet(): only values that differ from the defaults are stored, so a changed
// default (say the minimum duty) reaches every board that never overrode it.
void settingsSaveAll() {
  Settings d;
  fillDefaults(d, false);
  Preferences p;
  if (!p.begin(NS, false)) return;
  auto u8 = [&](const char *key, uint8_t v, uint8_t def) {
    if (v == def) p.remove(key);
    else p.putUChar(key, v);
  };
  auto flag = [&](const char *key, bool v, bool def) {
    if (v == def) p.remove(key);
    else p.putBool(key, v);
  };
  u8("rampUp", g.rampUp, d.rampUp);
  u8("rampDown", g.rampDown, d.rampDown);
  u8("bootMode", g.bootMode, d.bootMode);
  flag("protect", g.protectControl, d.protectControl);
  u8("hagen", g.haGen, d.haGen);
  for (int i = 0; i < kPresets; i++) {
    char k[8];
    snprintf(k, sizeof k, "pre%d", i);
    u8(k, g.presets[i], d.presets[i]);
  }
  for (int i = 0; i < kFans; i++) {
    char k[12];
    snprintf(k, sizeof k, "c%dname", i);
    if (strcmp(g.ch[i].name, d.ch[i].name) == 0) p.remove(k);
    else p.putString(k, g.ch[i].name);
    snprintf(k, sizeof k, "c%den", i);
    flag(k, g.ch[i].enabled, d.ch[i].enabled);
    snprintf(k, sizeof k, "c%dmin", i);
    u8(k, g.ch[i].minPct, d.ch[i].minPct);
    snprintf(k, sizeof k, "c%dmax", i);
    u8(k, g.ch[i].maxPct, d.ch[i].maxPct);
    snprintf(k, sizeof k, "c%dtach", i);
    flag(k, g.ch[i].tach, d.ch[i].tach);
    snprintf(k, sizeof k, "c%dppr", i);
    u8(k, g.ch[i].ppr, d.ch[i].ppr);
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
