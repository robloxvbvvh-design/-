package com.mobilecraft.launcher;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import java.io.File;

/** Launcher settings: nickname, character, model and game version. */
public final class Prefs {

    public static final String MODEL_CLASSIC = "classic";
    public static final String MODEL_SLIM = "slim";
    public static final String DEFAULT_VERSION = "1.21.1";

    private final SharedPreferences sp;
    private final Context context;

    public Prefs(Context context) {
        this.context = context.getApplicationContext();
        this.sp = context.getSharedPreferences("launcher", Context.MODE_PRIVATE);
    }

    public String nickname() { return sp.getString("nickname", "Steve"); }
    public void setNickname(String v) { sp.edit().putString("nickname", v).apply(); }

    public String characterId() { return sp.getString("character", "steve"); }
    public void setCharacterId(String v) { sp.edit().putString("character", v).apply(); }

    public String model() { return sp.getString("model", MODEL_CLASSIC); }
    public void setModel(String v) { sp.edit().putString("model", v).apply(); }
    public boolean isSlim() { return MODEL_SLIM.equals(model()); }

    public String version() { return sp.getString("version", DEFAULT_VERSION); }
    public void setVersion(String v) { sp.edit().putString("version", v).apply(); }

    public File customSkinFile() {
        return new File(context.getFilesDir(), "custom_skin.png");
    }

    /** The skin bitmap for a character; the custom one is read from disk. */
    public Bitmap skinFor(String characterId, boolean slim) {
        if (Character.CUSTOM_ID.equals(characterId)) {
            File f = customSkinFile();
            if (f.exists()) {
                Bitmap b = BitmapFactory.decodeFile(f.getAbsolutePath());
                if (b != null) return b;
            }
            characterId = "steve";
        }
        return SkinGenerator.generate(Character.find(Character.builtIn(), characterId), slim);
    }

    public String characterName(String characterId) {
        if (Character.CUSTOM_ID.equals(characterId)) return "Свой скин";
        return Character.find(Character.builtIn(), characterId).name;
    }
}
