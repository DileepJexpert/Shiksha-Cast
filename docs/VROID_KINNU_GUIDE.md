# Making 3D Kinnu in VRoid Studio (beginner guide)

Goal: build a cute 3D Indian girl ("Kinnu 3D") with **no modeling skills**, then export
one file (`.vrm`) that I turn into animated episodes. This is the only step you do by
hand — everything after (posing, lip-sync, rendering) I automate.

Time: ~30–60 minutes.

---

## Step 1 — Install VRoid Studio (free)

1. Go to **https://vroid.com/en/studio** → click **Download** (Windows).
   (Or get "VRoid Studio" free on **Steam**.)
2. Install and open it.

---

## Step 2 — Create a new female character

1. Click **Create New** → choose the **Female** base.
2. You'll see the girl in the middle and tabs on top: **Face, Hair, Body, Outfit, Look**.

---

## Step 3 — Make her look like Indian Kinnu

Work tab by tab. Don't aim for perfection — get close.

**Skin (Face tab → Skin):**
- Pick a **warm brown** skin tone (Indian). Slide toward tan/brown.

**Eyes (Face tab → Eye):**
- Big, friendly, **dark brown** eyes. Pick a round cute eye preset.
- Eyebrows: natural black.

**Hair (Hair tab):**
- Choose a **black** preset with a **side ponytail** (or a ponytail preset).
- Color: black. (A pink bow is optional — VRoid has hair accessories; skip if fiddly.)

**Body (Body tab):**
- Use the **child / shorter** proportions if available, or shrink height a bit so she
  reads as a kid (not a teen). Keep it simple.

**Outfit (Outfit tab):**
- Pick a simple **dress** preset. Set its color to **yellow**.
- Shoes: **blue** if there's an option.

**Look tab:** just check she looks cute and Indian. Good enough is good enough.

---

## Step 4 — (Important) Expressions for lip-sync

VRoid characters already include the mouth/expression shapes I need (A, I, U, E, O,
blink, smile). You don't have to do anything here — just **don't delete** the default
expressions. (If there's an "Expression" editor, leave it as-is.)

---

## Step 5 — Export the `.vrm` file

1. Top right: **Export** → **Export as VRM**.
2. In the export dialog:
   - Author name: anything (e.g. "Katixo").
   - **VRM version: choose VRM 0.0** (best compatibility with Blender). If only VRM 1.0
     is offered, that's fine too — tell me which one.
   - Leave reduction/optimization at defaults.
3. Save the file as:
   ```
   C:\dileepkm\Learning\Shiksha-Cast\assets\cartoon\characters3d\kinnu\kinnu.vrm
   ```
   (Create the folders if the Save dialog doesn't — or just save to Desktop and tell me;
   I'll move it.)

---

## Step 6 — Tell me "done"

Reply **"vrm done"** (and which VRM version you picked). Then I will:
1. Import her into Blender,
2. Hook up walk / wave / point / cheer + head turns,
3. Drive her mouth from the Kokoro voice (lip-sync),
4. Render a short test scene so you can see 3D Kinnu move,
5. If you like it, wire her into the full episode pipeline (story → video).

---

### Notes
- Keep the `.vrm` — it's your reusable character forever (any pose, any angle).
- If VRoid feels hard, even a rough version is fine for our first test; we refine later.
- A pink hair-bow and exact dress shape can be tuned later; don't get stuck on them.
