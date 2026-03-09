// Android logger — routes through logcat via __android_log_print
#include <os/logger.h>
#include <android/log.h>
#include <string>

#define LIBERTY_LOG_TAG "LibertyRecomp"

void os::logger::Init()
{
    __android_log_print(ANDROID_LOG_INFO, LIBERTY_LOG_TAG,
        "LibertyRecomp logger initialized (logcat)");
}

void os::logger::Log(const std::string_view str, ELogType type, const char* func)
{
    android_LogPriority prio;
    switch (type)
    {
    case ELogType::Warning: prio = ANDROID_LOG_WARN;  break;
    case ELogType::Error:   prio = ANDROID_LOG_ERROR; break;
    default:                prio = ANDROID_LOG_DEBUG; break;
    }

    std::string s(str);
    if (func)
        __android_log_print(prio, LIBERTY_LOG_TAG, "[%s] %s", func, s.c_str());
    else
        __android_log_print(prio, LIBERTY_LOG_TAG, "%s", s.c_str());
}
