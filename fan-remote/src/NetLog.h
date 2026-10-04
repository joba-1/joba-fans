// NetLog.h — logging to Serial and UDP syslog, plus the status of external resources.
#pragma once
#include <Arduino.h>

enum LogLevel { LOG_ERROR = 3, LOG_WARN = 4, LOG_INFO = 6, LOG_DEBUG = 7 };  // syslog severities

void logf(LogLevel lvl, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
void netlogLoop();   // re-resolves the syslog host hourly and after a failure

// What the status query reports for each external resource.
struct ResourceStatus {
  char status[48] = "unused";   // last result, e.g. "connected", "rc=-2", "resolve failed"
  uint32_t lastOkMs = 0;        // millis() of the last success, 0 = never
  uint32_t lastTryMs = 0;
};
ResourceStatus &resMqtt();
ResourceStatus &resSyslog();
ResourceStatus &resNtp();
void resSet(ResourceStatus &r, bool ok, const char *what);
