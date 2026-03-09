// iOS logger — routes through os_log (unified logging, visible in Console.app / Xcode console)
#include <os/logger.h>

#include <cstdio>
#include <string>
#include <os/log.h>

static os_log_t g_log = nullptr;

void os::logger::Init()
{
    g_log = os_log_create("com.libertyrecomp.app", "general");
}

void os::logger::Log(const std::string_view str, ELogType type, const char* func)
{
    os_log_type_t logType;
    switch (type)
    {
    case ELogType::Warning: logType = OS_LOG_TYPE_DEFAULT; break;
    case ELogType::Error:   logType = OS_LOG_TYPE_ERROR;   break;
    default:                logType = OS_LOG_TYPE_DEBUG;   break;
    }

    if (func)
        os_log_with_type(g_log, logType, "[%{public}s] %{public}s", func, std::string(str).c_str());
    else
        os_log_with_type(g_log, logType, "%{public}s", std::string(str).c_str());

    // Also write to stderr so Xcode's debug console picks it up
    if (func)
        fprintf(stderr, "[%s] %s\n", func, std::string(str).c_str());
    else
        fprintf(stderr, "%s\n", std::string(str).c_str());
}
