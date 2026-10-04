#include "NetLog.h"

#include <WiFi.h>
#include <WiFiUdp.h>

#include "Settings.h"

static ResourceStatus mqtt_, syslog_, ntp_;
ResourceStatus &resMqtt() { return mqtt_; }
ResourceStatus &resSyslog() { return syslog_; }
ResourceStatus &resNtp() { return ntp_; }

void resSet(ResourceStatus &r, bool ok, const char *what) {
  strncpy(r.status, what, sizeof r.status - 1);
  r.status[sizeof r.status - 1] = 0;
  r.lastTryMs = millis() ? millis() : 1;
  if (ok) r.lastOkMs = r.lastTryMs;
}

static WiFiUDP udp;
static IPAddress sysIp;
static bool sysIpValid = false;
static uint32_t lastResolve = 0;

static bool resolveSyslog() {
  lastResolve = millis();
  const char *h = settings().syslogHost;
  if (!h[0]) {
    sysIpValid = false;
    resSet(syslog_, false, "unused");
    syslog_.lastTryMs = 0;
    return false;
  }
  sysIpValid = WiFi.hostByName(h, sysIp) == 1;
  if (!sysIpValid) resSet(syslog_, false, "resolve failed");
  return sysIpValid;
}

void netlogLoop() {
  if (WiFi.status() != WL_CONNECTED || !settings().syslogHost[0]) return;
  uint32_t age = millis() - lastResolve;
  if (!sysIpValid ? age > 30000 : age > 3600000UL) resolveSyslog();
}

static const char *const kNames[] = {"", "", "", "ERROR", "WARN", "", "INFO", "DEBUG"};

void logf(LogLevel lvl, const char *fmt, ...) {
  char msg[160];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(msg, sizeof msg, fmt, ap);
  va_end(ap);

  Serial.printf("[%lu] %s %s\n", (unsigned long)millis(), kNames[lvl], msg);

  if (lvl > LOG_INFO || WiFi.status() != WL_CONNECTED || !settings().syslogHost[0]) return;
  if (!sysIpValid && !resolveSyslog()) return;

  // RFC 5424: <PRI>1 TIMESTAMP HOST APP - - - MSG, facility local0 (16)
  char ts[32] = "-";
  time_t now = time(nullptr);
  if (now > 1700000000) {
    struct tm tmv;
    gmtime_r(&now, &tmv);
    strftime(ts, sizeof ts, "%Y-%m-%dT%H:%M:%SZ", &tmv);
  }
  char line[260];
  int n = snprintf(line, sizeof line, "<%d>1 %s %s fan-remote - - - %s", 16 * 8 + lvl, ts,
                   deviceId(), msg);
  if (n <= 0) return;
  bool ok = udp.beginPacket(sysIp, CFG_SYSLOG_PORT) && udp.write((const uint8_t *)line, n) == (size_t)n &&
            udp.endPacket();
  resSet(syslog_, ok, ok ? "sent" : "send failed");
  if (!ok) sysIpValid = false;  // resolve again next time
}
