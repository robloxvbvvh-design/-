package com.mobilecraft.launcher;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Builds the JVM command line for an installed version in offline mode. */
public final class LaunchCommand {

    private LaunchCommand() {}

    /** Offline UUID, computed the same way as the vanilla server does. */
    public static UUID offlineUuid(String nickname) {
        return UUID.nameUUIDFromBytes(("OfflinePlayer:" + nickname).getBytes(StandardCharsets.UTF_8));
    }

    public static List<String> build(File gameDir, String versionId, String nickname) throws Exception {
        JSONObject v = new JSONObject(GameInstaller.readFile(GameInstaller.versionJson(gameDir, versionId)));

        StringBuilder cp = new StringBuilder();
        JSONArray libs = v.optJSONArray("libraries");
        if (libs != null) {
            for (int i = 0; i < libs.length(); i++) {
                JSONObject lib = libs.getJSONObject(i);
                if (!GameInstaller.rulesAllow(lib.optJSONArray("rules"))) continue;
                JSONObject dl = lib.optJSONObject("downloads");
                JSONObject art = dl == null ? null : dl.optJSONObject("artifact");
                if (art == null) continue;
                cp.append(new File(gameDir, "libraries/" + art.getString("path"))).append(':');
            }
        }
        cp.append(GameInstaller.clientJar(gameDir, versionId));

        JSONObject assetIndex = v.optJSONObject("assetIndex");
        Map<String, String> vars = new HashMap<>();
        vars.put("auth_player_name", nickname);
        vars.put("version_name", versionId);
        vars.put("game_directory", gameDir.getAbsolutePath());
        vars.put("assets_root", new File(gameDir, "assets").getAbsolutePath());
        vars.put("game_assets", new File(gameDir, "assets").getAbsolutePath());
        vars.put("assets_index_name", assetIndex == null ? "legacy" : assetIndex.optString("id"));
        vars.put("auth_uuid", offlineUuid(nickname).toString().replace("-", ""));
        vars.put("auth_access_token", "0");
        vars.put("auth_session", "0");
        vars.put("clientid", "0");
        vars.put("auth_xuid", "0");
        vars.put("user_type", "legacy");
        vars.put("user_properties", "{}");
        vars.put("version_type", v.optString("type", "release"));

        List<String> cmd = new ArrayList<>();
        cmd.add("java");
        cmd.add("-Xmx2G");
        cmd.add("-Djava.library.path=" + new File(gameDir, "natives"));
        cmd.add("-cp");
        cmd.add(cp.toString());
        cmd.add(v.getString("mainClass"));

        if (v.has("minecraftArguments")) {
            // Versions before 1.13.
            for (String arg : v.getString("minecraftArguments").split(" ")) cmd.add(substitute(arg, vars));
        } else {
            JSONArray game = v.getJSONObject("arguments").getJSONArray("game");
            for (int i = 0; i < game.length(); i++) {
                Object o = game.get(i);
                if (o instanceof String) cmd.add(substitute((String) o, vars));
                // Rule-based arguments (demo mode, custom resolution, quick play) are skipped.
            }
        }
        return cmd;
    }

    private static String substitute(String arg, Map<String, String> vars) {
        for (Map.Entry<String, String> e : vars.entrySet()) {
            arg = arg.replace("${" + e.getKey() + "}", e.getValue());
        }
        return arg;
    }
}
