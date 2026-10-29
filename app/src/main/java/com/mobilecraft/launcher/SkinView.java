package com.mobilecraft.launcher;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.View;

/**
 * Draws a Minecraft skin as a flat front or back view (16x32 skin pixels).
 * Supports classic (4px arms) and slim (3px arms) models, 64x64 and legacy 64x32 skins.
 * Tapping the view turns the character around.
 */
public class SkinView extends View {

    private final Paint paint = new Paint();
    private final Paint shadow = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Rect src = new Rect();
    private final RectF dst = new RectF();

    private Bitmap skin;
    private boolean slim;
    private boolean back;
    private float turn = 1f; // horizontal scale used for the turn-around animation

    public SkinView(Context context) {
        this(context, null);
    }

    public SkinView(Context context, AttributeSet attrs) {
        super(context, attrs);
        paint.setFilterBitmap(false);
        paint.setAntiAlias(false);
        paint.setDither(false);
        shadow.setColor(0x55000000);
    }

    public void setSkin(Bitmap skin, boolean slim) {
        this.skin = skin;
        this.slim = slim;
        invalidate();
    }

    /** Makes the view turn around when tapped. */
    public void enableTurnOnTap() {
        setClickable(true);
        setOnClickListener(v -> turnAround());
    }

    public void turnAround() {
        ValueAnimator anim = ValueAnimator.ofFloat(1f, -1f);
        anim.setDuration(350);
        final boolean[] switched = {false};
        anim.addUpdateListener(a -> {
            float f = (Float) a.getAnimatedValue();
            if (!switched[0] && f <= 0f) {
                switched[0] = true;
                back = !back;
            }
            turn = Math.abs(f);
            invalidate();
        });
        anim.start();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (skin == null) return;

        float w = getWidth() - getPaddingLeft() - getPaddingRight();
        float h = getHeight() - getPaddingTop() - getPaddingBottom();
        // 16 x 32 skin pixels plus a little room for the shadow.
        float s = Math.min(w / 16f, h / 33f);
        float ox = getPaddingLeft() + (w - 16 * s) / 2f;
        float oy = getPaddingTop() + (h - 33 * s) / 2f;

        canvas.drawOval(new RectF(ox + 2 * s, oy + 31.2f * s, ox + 14 * s, oy + 33 * s), shadow);

        canvas.save();
        canvas.scale(Math.max(turn, 0.02f), 1f, ox + 8 * s, 0);
        if (back) drawBack(canvas, ox, oy, s);
        else drawFront(canvas, ox, oy, s);
        canvas.restore();
    }

    private boolean isLegacy() {
        return skin.getHeight() == 32;
    }

    private void drawFront(Canvas c, float ox, float oy, float s) {
        int a = slim ? 3 : 4;
        boolean legacy = isLegacy();
        float armR = slim ? 1 : 0; // right arm (viewer's left) x position

        // Base layer.
        part(c, 8, 8, 8, 8, ox, oy, 4, 0, s, false);                 // head
        part(c, 20, 20, 8, 12, ox, oy, 4, 8, s, false);              // body
        part(c, 44, 20, a, 12, ox, oy, armR, 8, s, false);           // right arm
        part(c, 4, 20, 4, 12, ox, oy, 4, 20, s, false);              // right leg
        if (legacy) {
            part(c, 44, 20, a, 12, ox, oy, 12, 8, s, true);          // left arm (mirrored)
            part(c, 4, 20, 4, 12, ox, oy, 8, 20, s, true);           // left leg (mirrored)
        } else {
            part(c, 36, 52, a, 12, ox, oy, 12, 8, s, false);
            part(c, 20, 52, 4, 12, ox, oy, 8, 20, s, false);
        }

        // Overlay layer (hat, jacket, sleeves, trousers).
        part(c, 40, 8, 8, 8, ox, oy, 4, 0, s, false);
        if (!legacy) {
            part(c, 20, 36, 8, 12, ox, oy, 4, 8, s, false);
            part(c, 44, 36, a, 12, ox, oy, armR, 8, s, false);
            part(c, 52, 52, a, 12, ox, oy, 12, 8, s, false);
            part(c, 4, 36, 4, 12, ox, oy, 4, 20, s, false);
            part(c, 4, 52, 4, 12, ox, oy, 8, 20, s, false);
        }
    }

    private void drawBack(Canvas c, float ox, float oy, float s) {
        int a = slim ? 3 : 4;
        boolean legacy = isLegacy();
        int rBack = slim ? 51 : 52;   // right arm back u
        int lBack = slim ? 43 : 44;   // left arm back u
        float armR = 12;              // from behind the right arm is on the viewer's right
        float armL = slim ? 1 : 0;

        part(c, 24, 8, 8, 8, ox, oy, 4, 0, s, false);                // head
        part(c, 32, 20, 8, 12, ox, oy, 4, 8, s, false);              // body
        part(c, rBack, 20, a, 12, ox, oy, armR, 8, s, false);        // right arm
        part(c, 12, 20, 4, 12, ox, oy, 8, 20, s, false);             // right leg
        if (legacy) {
            part(c, rBack, 20, a, 12, ox, oy, armL, 8, s, true);
            part(c, 12, 20, 4, 12, ox, oy, 4, 20, s, true);
        } else {
            part(c, lBack, 52, a, 12, ox, oy, armL, 8, s, false);
            part(c, 28, 52, 4, 12, ox, oy, 4, 20, s, false);
        }

        part(c, 56, 8, 8, 8, ox, oy, 4, 0, s, false);
        if (!legacy) {
            part(c, 32, 36, 8, 12, ox, oy, 4, 8, s, false);
            part(c, rBack, 36, a, 12, ox, oy, armR, 8, s, false);
            part(c, lBack + 16, 52, a, 12, ox, oy, armL, 8, s, false);
            part(c, 12, 36, 4, 12, ox, oy, 8, 20, s, false);
            part(c, 12, 52, 4, 12, ox, oy, 4, 20, s, false);
        }
    }

    /** Copies a w x h region of the skin at (u,v) to skin-pixel position (x,y). */
    private void part(Canvas c, int u, int v, int w, int h,
                      float ox, float oy, float x, float y, float s, boolean mirror) {
        src.set(u, v, u + w, v + h);
        dst.set(ox + x * s, oy + y * s, ox + (x + w) * s, oy + (y + h) * s);
        if (mirror) {
            c.save();
            c.scale(-1f, 1f, dst.centerX(), 0);
            c.drawBitmap(skin, src, dst, paint);
            c.restore();
        } else {
            c.drawBitmap(skin, src, dst, paint);
        }
    }
}
