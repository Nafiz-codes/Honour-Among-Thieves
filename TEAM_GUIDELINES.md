# Honour Among Thieves — Team Development Guide

## Project Overview

**Honour Among Thieves** is a 3D stealth game built for CSE423 using PyOpenGL/GLUT. The player controls a thief stealing items to fund treatment for his sick mother. Core loop: sneak through rooms, manipulate light/darkness, avoid or trick guards (sight-based and sound-based), push/use obstacles for cover, and steal enough items to hit a quota. The game deliberately ends with the thief getting caught — the climax is a scripted capture cutscene followed by a final escape sequence from a police station.

This is a **stealth game, not a shooter** — no combat against guards. All tension comes from detection avoidance, environmental manipulation, and light control.

## Tech Constraints — Read Before Writing Any Code

- **Only use functions available in the course-provided GLUT template.** No external physics engines, no collision libraries, no third-party asset pipelines.
- `glDepth` / depth-buffer functions are allowed in addition to the template's function set.
- Any primitive drawing must use what the template already exposes (`glutSolidCube`, `glutSolidSphere`, `glutSolidCone`, `glutWireCube`, `GL_LINES`/`GL_TRIANGLES` immediate mode, etc.) unless the whole team agrees to add something new.
- **No new imports/libraries without a team discussion first.** If you think you need something outside the current stack, raise it in the group chat before writing code around it — don't just add it and hope no one notices.
- All effects (lighting, glow, detection radii, cutscene camera moves) should be done with primitive geometry, color/alpha changes, and transform math — not shaders, unless confirmed otherwise as in-scope.

## How We're Using Antigravity

Each member runs their own local Antigravity instance. When you start a session:

1. Tell your agent **your name** explicitly.
2. Point it at **this file** for full project context.
3. Ask it to work **only** on your assigned feature set below — not anyone else's, even if you can see it in the repo.

## Ground Rules (Everyone, No Exceptions)

1. **Stay in your lane.** Only touch files, functions, or logic tied to your own assigned features. If someone else's code looks buggy or improvable, flag it to them — don't edit it yourself.
2. **Never change existing working code** outside your own feature, even refactors "to make it cleaner." If a shared function needs a change, ask the team first (see Shared Systems below).
3. **One feature at a time, then stop for review.** After finishing a single feature (not your whole list), stop and show it to the team before starting the next one. Don't batch multiple features into one big unreviewed dump.
4. **No silent scope creep.** If a feature naturally needs something not on your list (e.g. a new shared constant, a new game state), flag it — don't just build it in isolation.
5. **Commit discipline.** One feature per commit where possible. Write commit messages that name the feature, e.g. `feat(ahona): obstacle push physics for boxes`.
6. **Stick to the allowed library list above.** If your agent suggests using something outside the template's functions, don't accept it without checking with the team.
7. **Keep naming/style consistent.** Match existing function/variable naming conventions already in the repo rather than introducing your own pattern.
8. **Test before marking a feature done.** Run the game locally and confirm your feature works in isolation and doesn't crash the base template before asking for review.

## Shared Systems — Flag Before Touching

These will likely be touched by more than one person's features. If your work needs a change here, post in the group chat first so no one overwrites someone else's edit:

- Game state management (tutorial → stealing area → capture cutscene → police station escape → win/lose)
- HUD/text rendering (points, health bar, inventory display all draw to the same HUD space)
- Shared constants (movement speed, detection radius values, room boundary coordinates)
- Camera control handoff (player free-look vs. scripted cutscene camera vs. throw-aim camera)

## Feature Assignments

### Ahona
1. Interactive obstacle design — closet, dumpster, box (extensible for more later)
2. Obstacle physics — pushing/moving obstacles for player use (cover, blocking guard paths, reaching loot)
3. Darkness / light physics — light objects with on/off state and radius, darkness effect on surrounding area (not the projectile that turns lights off — that's Mehrab's)
4. Stealing objects — collectible item objects placed in the world, pickup interaction

### Nafiz
1. Background/level design — police station, stealing area, tutorial area
2. Police AI — enemy behavior logic (patrol, suspicious, alert/chase states)
3. Field of view for police — sight-based guard detection cone
4. Hearing circle for police — sound-based guard detection radius
5. Points system, health bar, and inventory (Minecraft-style grid inventory for stolen items)
6. Game state machine — transitions between tutorial, stealing area, capture cutscene, police station escape, win/lose
7. Cutscene system — scripted camera takeover, disabled player input, capture sequence, escape climax
8. Win/lose screens

### Mehrab
1. Player model design, police model design
2. Projectile mechanic to shoot out/turn off lights (the projectile itself, not the light's darkness physics)
3. Character movement physics
4. Camera system — player's first/third-person FOV and control
5. Object throwing — throwable distraction items (stones/bottles) that lure police to the thrown location
6. Wall/boundary collision — general level geometry collision so player and objects can't pass through walls

## Review Checklist Before Marking a Feature Complete

- [ ] Feature works standalone without crashing the base template
- [ ] No other member's files/functions were modified
- [ ] No new imports/libraries were added without team approval
- [ ] Naming matches existing repo conventions
- [ ] Shared systems (state, HUD, constants, camera handoff) were not changed without flagging the team first
- [ ] Feature shown to the team for review before starting the next one
