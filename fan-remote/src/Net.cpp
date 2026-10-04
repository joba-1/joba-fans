#include "Net.h"

#include <ArduinoOTA.h>
#include <ESPmDNS.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <esp_sntp.h>

#include "NetLog.h"
#include "Settings.h"

static WiFiManager wm;
static bool servicesUp = false;
static uint32_t lastSupervise = 0;
static char apName[32];

// Custom portal fields; their values are read in the save callback.
static WiFiManagerParameter *pName, *pMqtt, *pPass;

static void onSaveParams() {
  Settings &s = settings();
  auto take = [](char *dst, size_t n, const char *v) {
    if (!v || !*v) return false;
    strncpy(dst, v, n - 1);
    dst[n - 1] = 0;
    return true;
  };
  bool any = false;
  any |= take(s.name, sizeof s.name, pName->getValue());
  any |= take(s.mqttHost, sizeof s.mqttHost, pMqtt->getValue());
  // Only an acceptable password replaces the current one; an empty field keeps it.
  const char *pw = pPass->getValue();
  if (pw && strlen(pw) >= 8) any |= take(s.adminPass, sizeof s.adminPass, pw);
  if (any) settingsSaveNet();
  logf(LOG_INFO, "setup portal: settings saved");
}

static void sntpSynced(struct timeval *) { resSet(resNtp(), true, "synced"); }

static void startServices() {
  if (servicesUp) return;
  servicesUp = true;
  MDNS.begin(deviceId());
  MDNS.addService("http", "tcp", 80);
  configTzTime(CFG_TIMEZONE, settings().ntpHost);
  sntp_set_time_sync_notification_cb(sntpSynced);
  resSet(resNtp(), false, "waiting");

  ArduinoOTA.setHostname(deviceId());
  ArduinoOTA.setPassword(settings().adminPass);
  ArduinoOTA.onStart([]() { logf(LOG_INFO, "OTA start"); });
  ArduinoOTA.onEnd([]() { logf(LOG_INFO, "OTA done"); });
  ArduinoOTA.begin();
  logf(LOG_INFO, "online: %s ip %s rssi %d", deviceId(), WiFi.localIP().toString().c_str(),
       WiFi.RSSI());
}

void netBegin() {
  snprintf(apName, sizeof apName, "%s-setup", deviceId());
  WiFi.mode(WIFI_STA);
  WiFi.setHostname(deviceId());
  WiFi.setAutoReconnect(true);

  // Portal fields: friendly name, broker, admin password (also the AP and OTA password).
  static WiFiManagerParameter name("name", "Device name", settings().name, 31);
  static WiFiManagerParameter mqtt("mqtt", "MQTT broker (host or alias)", settings().mqttHost, 63);
  static WiFiManagerParameter pass("pass", "New admin password (min 8, empty = keep)", "", 47,
                                   "type=\"password\" autocomplete=\"new-password\"");
  pName = &name;
  pMqtt = &mqtt;
  pPass = &pass;
  wm.addParameter(&name);
  wm.addParameter(&mqtt);
  wm.addParameter(&pass);
  wm.setSaveParamsCallback(onSaveParams);
  wm.setHostname(deviceId());
  wm.setTitle("fan-remote");
  wm.setConnectTimeout(20);
  wm.setConfigPortalBlocking(false);  // the fans are on their own task anyway; stay responsive
  wm.setConfigPortalTimeout(0);       // portal stays open until somebody configures it
  wm.setCaptivePortalEnable(true);

  if (wm.autoConnect(apName, settings().adminPass)) startServices();
  else logf(LOG_WARN, "no WiFi yet; setup portal %s is open", apName);
}

void netLoop() {
  wm.process();
  if (WiFi.status() == WL_CONNECTED) {
    if (!servicesUp) startServices();
    ArduinoOTA.handle();
    return;
  }
  // Not connected: reconnect, or reopen the portal if there are no credentials at all.
  if (millis() - lastSupervise > 30000 && !wm.getConfigPortalActive()) {
    lastSupervise = millis();
    if (WiFi.SSID().length() == 0) wm.autoConnect(apName, settings().adminPass);
    else WiFi.reconnect();
  }
}

bool netConnected() { return WiFi.status() == WL_CONNECTED; }
bool netPortalActive() { return wm.getConfigPortalActive(); }

void netForgetWifi() {
  wm.resetSettings();
  // A reboot is the clean way to hand port 80 back to the setup portal (the web server
  // only starts once WiFi is up). It lets the PWM pins float briefly; this is a rare
  // admin action.
  logf(LOG_WARN, "WiFi credentials erased, restarting into the setup portal");
  WiFi.disconnect(false, true);
  delay(200);
  ESP.restart();
}
