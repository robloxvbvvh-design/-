package com.mobilecraft.launcher;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.regex.Pattern;

public class MainActivity extends Activity {

    private static final Pattern NICK = Pattern.compile("[A-Za-z0-9_]{3,16}");
    /** Android port of the Java Edition runtime that can actually run the game. */
    private static final String POJAV_PACKAGE = "net.kdt.pojavlaunch";

    private Prefs prefs;
    private SkinView preview;
    private TextView characterName, modelName, status;
    private EditText nickname;
    private Button btnVersion, btnPlay, btnCharacter;
    private ProgressBar progress;
    private GameInstaller installer;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        prefs = new Prefs(this);

        preview = findViewById(R.id.skin_preview);
        characterName = findViewById(R.id.character_name);
        modelName = findViewById(R.id.model_name);
        status = findViewById(R.id.status);
        nickname = findViewById(R.id.nickname);
        btnCharacter = findViewById(R.id.btn_character);
        btnVersion = findViewById(R.id.btn_version);
        btnPlay = findViewById(R.id.btn_play);
        progress = findViewById(R.id.progress);

        nickname.setText(prefs.nickname());
        preview.enableTurnOnTap();

        btnCharacter.setOnClickListener(v -> startActivity(new Intent(this, CharacterActivity.class)));
        btnVersion.setOnClickListener(v -> startActivity(new Intent(this, VersionActivity.class)));
        btnPlay.setOnClickListener(v -> {
            if (installer != null) {
                installer.cancel();
            } else {
                play();
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshUi();
    }

    private void refreshUi() {
        String id = prefs.characterId();
        preview.setSkin(prefs.skinFor(id, prefs.isSlim()), prefs.isSlim());
        characterName.setText(prefs.characterName(id));
        modelName.setText(prefs.isSlim() ? "Модель: тонкая (Alex)" : "Модель: классическая (Steve)");
        String v = prefs.version();
        btnVersion.setText("Версия: " + v
                + (GameInstaller.isInstalled(gameDir(), v) ? "  ✓ установлена" : ""));
    }

    @Override
    protected void onPause() {
        super.onPause();
        String nick = nickname.getText().toString().trim();
        if (NICK.matcher(nick).matches()) prefs.setNickname(nick);
    }

    @Override
    protected void onDestroy() {
        if (installer != null) installer.cancel();
        super.onDestroy();
    }

    private File gameDir() {
        File base = getExternalFilesDir(null);
        if (base == null) base = getFilesDir();
        return new File(base, ".minecraft");
    }

    private void play() {
        String nick = nickname.getText().toString().trim();
        if (TextUtils.isEmpty(nick)) nick = nickname.getHint().toString();
        if (!NICK.matcher(nick).matches()) {
            nickname.setError("3–16 символов: латиница, цифры и _");
            return;
        }
        prefs.setNickname(nick);

        String version = prefs.version();
        if (GameInstaller.isInstalled(gameDir(), version)) {
            launch(version, nick);
            return;
        }

        final String player = nick;
        setBusy(true);
        installer = new GameInstaller(gameDir());
        installer.install(version, new GameInstaller.Listener() {
            @Override
            public void onProgress(String message, int done, int total) {
                status.setText(total > 1 ? message + " " + done + "/" + total : message);
                progress.setProgress(total > 0 ? (int) (1000L * done / total) : 0);
            }

            @Override
            public void onFinished(File versionJson) {
                installer = null;
                setBusy(false);
                refreshUi();
                launch(version, player);
            }

            @Override
            public void onError(Exception e) {
                installer = null;
                setBusy(false);
                status.setVisibility(View.VISIBLE);
                status.setText(e instanceof InterruptedException
                        ? "Загрузка отменена"
                        : "Ошибка: " + e.getMessage());
            }
        });
    }

    private void setBusy(boolean busy) {
        progress.setVisibility(busy ? View.VISIBLE : View.GONE);
        status.setVisibility(busy ? View.VISIBLE : View.GONE);
        progress.setProgress(0);
        btnPlay.setText(busy ? "ОТМЕНА" : getString(R.string.play));
        btnCharacter.setEnabled(!busy);
        btnVersion.setEnabled(!busy);
        nickname.setEnabled(!busy);
    }

    /**
     * Prepares the launch command. Running the desktop Java client needs an Android build of
     * the JVM plus an OpenGL→GLES translation layer; if PojavLauncher is installed we hand off to it.
     */
    private void launch(String version, String nick) {
        final String command;
        try {
            List<String> cmd = LaunchCommand.build(gameDir(), version, nick);
            command = TextUtils.join(" ", cmd);
            try (FileOutputStream out = new FileOutputStream(new File(gameDir(), "launch_command.txt"))) {
                out.write(command.getBytes(StandardCharsets.UTF_8));
            }
        } catch (Exception e) {
            Toast.makeText(this, "Ошибка подготовки запуска: " + e.getMessage(), Toast.LENGTH_LONG).show();
            return;
        }

        final Intent pojav = getPackageManager().getLaunchIntentForPackage(POJAV_PACKAGE);
        AlertDialog.Builder b = new AlertDialog.Builder(this)
                .setTitle("Minecraft " + version + " готов")
                .setMessage("Игрок: " + nick + "\n"
                        + "Персонаж: " + prefs.characterName(prefs.characterId())
                        + (prefs.isSlim() ? " (тонкая модель)" : " (классическая модель)") + "\n\n"
                        + "Файлы игры загружены в:\n" + gameDir() + "\n\n"
                        + (pojav != null
                            ? "Нажмите «Запустить», чтобы открыть игру через PojavLauncher."
                            : "Для запуска Java-версии на телефоне нужна среда Java для Android "
                              + "(например, PojavLauncher). Установите её, и лаунчер будет "
                              + "передавать ей запуск."))
                .setNeutralButton("Копировать команду", (d, w) -> {
                    ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                    cm.setPrimaryClip(ClipData.newPlainText("launch", command));
                    Toast.makeText(this, "Команда запуска скопирована", Toast.LENGTH_SHORT).show();
                })
                .setNegativeButton("Закрыть", null);
        if (pojav != null) {
            b.setPositiveButton("Запустить", (d, w) -> startActivity(pojav));
        }
        b.show();
    }
}
