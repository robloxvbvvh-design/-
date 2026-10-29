package com.mobilecraft.launcher;

import android.graphics.Bitmap;

/** Paints a 64x64 Minecraft skin (1.8+ layout) from a {@link Character}'s colors. */
public final class SkinGenerator {

    private static final int W = 64;

    private SkinGenerator() {}

    public static Bitmap generate(Character c, boolean slim) {
        int[] px = new int[W * W];
        int arm = slim ? 3 : 4;

        // Head (all six faces), 8x8x8 box at (0,0).
        box(px, 0, 0, 8, 8, 8, c.skin);
        paintHead(px, c);

        // Body 8x12x4 at (16,16), legs 4x12x4, arms arm x12x4.
        box(px, 16, 16, 8, 12, 4, c.shirt);
        box(px, 0, 16, 4, 12, 4, c.pants);   // right leg
        box(px, 16, 48, 4, 12, 4, c.pants);  // left leg
        box(px, 40, 16, arm, 12, 4, c.skin); // right arm
        box(px, 32, 48, arm, 12, 4, c.skin); // left arm

        // Sleeves: top 4 rows of the arms.
        sleeve(px, 40, 16, arm, c.shirt);
        sleeve(px, 32, 48, arm, c.shirt);

        // Shoes: bottom 2 rows of the legs.
        rowsOfBox(px, 0, 16, 4, 12, 4, 10, 2, c.shoes);
        rowsOfBox(px, 16, 48, 4, 12, 4, 10, 2, c.shoes);

        // Shirt details on the body front: collar and belt.
        rect(px, 23, 20, 2, 3, c.shirtDetail);
        rect(px, 20, 30, 8, 1, c.shirtDetail);

        Bitmap bmp = Bitmap.createBitmap(W, W, Bitmap.Config.ARGB_8888);
        bmp.setPixels(px, 0, W, 0, 0, W, W);
        return bmp;
    }

    private static void paintHead(int[] px, Character c) {
        // Front face is at (8,8).
        int fx = 8, fy = 8;
        if (c.hairStyle == 2) {
            // Helmet / hood: covers everything except a band around the eyes.
            box(px, 0, 0, 8, 8, 8, c.hair);
            rect(px, fx + 1, fy + 3, 6, 3, c.skin);
        } else {
            rect(px, 8, 0, 8, 8, c.hair);           // top
            rect(px, 24, 8, 8, c.hairStyle == 1 ? 8 : 6, c.hair); // back
            rect(px, fx, fy, 8, 2, c.hair);         // fringe
            rect(px, 0, 8, 8, 3, c.hair);           // right side
            rect(px, 16, 8, 8, 3, c.hair);          // left side
            if (c.hairStyle == 1) {
                rect(px, 0, 8, 3, 8, c.hair);
                rect(px, 21, 8, 3, 8, c.hair);
                rect(px, fx, fy + 2, 1, 4, c.hair);
                rect(px, fx + 7, fy + 2, 1, 4, c.hair);
            }
        }
        // Eyes: white + iris.
        rect(px, fx + 1, fy + 4, 1, 1, 0xFFFFFFFF);
        rect(px, fx + 2, fy + 4, 1, 1, c.eyes);
        rect(px, fx + 5, fy + 4, 1, 1, c.eyes);
        rect(px, fx + 6, fy + 4, 1, 1, 0xFFFFFFFF);
        // Mouth.
        if (c.hairStyle != 2) {
            rect(px, fx + 3, fy + 6, 2, 1, darken(c.skin, 0.65f));
        }
    }

    /** Fills all six faces of a skin box whose texture origin is (u,v). */
    private static void box(int[] px, int u, int v, int w, int h, int d, int color) {
        rect(px, u + d, v, w, d, color);            // top
        rect(px, u + d + w, v, w, d, color);        // bottom
        rect(px, u, v + d, d + w + d + w, h, color); // right, front, left, back
    }

    private static void sleeve(int[] px, int u, int v, int w, int color) {
        rowsOfBox(px, u, v, w, 12, 4, 0, 4, color);
        rect(px, u + 4, v, w, 4, color); // top of the arm
    }

    /** Fills rows [from, from+count) of the four side faces of a box. */
    private static void rowsOfBox(int[] px, int u, int v, int w, int h, int d,
                                  int from, int count, int color) {
        rect(px, u, v + d + from, d + w + d + w, count, color);
    }

    private static void rect(int[] px, int x, int y, int w, int h, int color) {
        for (int j = y; j < y + h; j++) {
            for (int i = x; i < x + w; i++) {
                if (i >= 0 && i < W && j >= 0 && j < W) px[j * W + i] = color;
            }
        }
    }

    static int darken(int color, float f) {
        int r = (int) (((color >> 16) & 0xFF) * f);
        int g = (int) (((color >> 8) & 0xFF) * f);
        int b = (int) ((color & 0xFF) * f);
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }
}
