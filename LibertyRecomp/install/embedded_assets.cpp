#include "embedded_assets.h"
#include "platform_paths.h"

#include <fstream>
#include <filesystem>

// ── Platform-specific game root ─────────────────────────────────────────────
static std::filesystem::path ResolveEmbeddedGameRoot()
{
#if defined(__ORBIS__)
    return std::filesystem::path("/app0/game");
#elif defined(__SWITCH__)
    return std::filesystem::path("romfs:/game");
#elif defined(TARGET_OS_IOS) && TARGET_OS_IOS
    // Bundle resources are at <Bundle>/game/
    extern "C" const char* LIBERTY_IOS_GetBundlePath();
    const char* bp = LIBERTY_IOS_GetBundlePath();
    if (bp)
        return std::filesystem::path(bp) / "game";
    return std::filesystem::path("game");
#elif defined(__ANDROID__)
    // After first-boot extraction, files live in internal storage
    return PlatformPaths::GetGameDirectory();
#else
    // Desktop: embedded path is unused, fall back to normal install dir
    return PlatformPaths::GetGameDirectory();
#endif
}

// ────────────────────────────────────────────────────────────────────────────

bool EmbeddedAssets::IsAvailable()
{
#if defined(LIBERTY_RECOMP_EMBEDDED_ASSETS)
    return true;
#else
    return false;
#endif
}

std::filesystem::path EmbeddedAssets::GetGameRoot()
{
    static std::filesystem::path root = ResolveEmbeddedGameRoot();
    return root;
}

std::filesystem::path EmbeddedAssets::GetDLCRoot()
{
#if defined(LIBERTY_RECOMP_EMBEDDED_ASSETS)
    return GetGameRoot().parent_path() / "dlc";
#else
    return PlatformPaths::GetInstallDirectory() / "dlc";
#endif
}

EmbeddedAssets::Manifest EmbeddedAssets::ReadManifest()
{
    Manifest m;

    // The manifest JSON is written by CMake's configure_file into the package.
    // On embedded platforms it lives next to the game root as manifest.json.
    std::filesystem::path manifestPath = GetGameRoot().parent_path() / "manifest.json";

    std::ifstream f(manifestPath);
    if (!f.is_open())
        return m;

    // Minimal hand-rolled JSON parse to avoid pulling in a JSON library dependency
    std::string line;
    while (std::getline(f, line))
    {
        auto extract = [&](const std::string& key) -> std::string
        {
            auto pos = line.find("\"" + key + "\"");
            if (pos == std::string::npos) return {};
            auto colon = line.find(':', pos);
            if (colon == std::string::npos) return {};
            auto q1 = line.find('"', colon + 1);
            if (q1 == std::string::npos) return {};
            auto q2 = line.find('"', q1 + 1);
            if (q2 == std::string::npos) return {};
            return line.substr(q1 + 1, q2 - q1 - 1);
        };

        if (!extract("gameVersion").empty())     m.gameVersion     = extract("gameVersion");
        if (!extract("titleUpdate").empty())     m.titleUpdateVersion = extract("titleUpdate");
        if (line.find("\"hasTLAD\": true") != std::string::npos)  m.hasTLAD  = true;
        if (line.find("\"hasTBOGT\": true") != std::string::npos) m.hasTBOGT = true;

        {
            auto pos = line.find("\"buildTimestamp\"");
            if (pos != std::string::npos)
            {
                auto colon = line.find(':', pos);
                if (colon != std::string::npos)
                    m.buildTimestamp = static_cast<uint32_t>(std::stoul(line.substr(colon + 1)));
            }
        }
    }

    return m;
}

bool EmbeddedAssets::ExtractObbIfNeeded(const std::filesystem::path& obbPath,
                                         const std::filesystem::path& destPath)
{
#if defined(__ANDROID__)
    std::error_code ec;
    // If the marker file already exists, extraction was done on a previous boot.
    auto marker = destPath / ".obb_extracted";
    if (std::filesystem::exists(marker, ec))
        return true;

    // TODO: implement OBB zip extraction using minizip or libzip.
    // For now, log and return false so the caller can show an error.
    (void)obbPath;
    (void)destPath;
    return false;
#else
    (void)obbPath;
    (void)destPath;
    return true; // Not needed on non-Android platforms
#endif
}
