# mj41.cz

Source of [mj41.cz](https://mj41.cz) — a single hand-written page, no build step.

- **[docs/](docs/)** — the site itself; GitHub Pages publishes this folder.
- **[tools/](tools/)** — how the green PMD 85 screens on the page were made:
  a container that runs the real machine and types the 1991/92 program into it,
  and a script that turns the captured bitmap into something that looks like a
  photo of the monitor. See [tools/pmd85-emulator/](tools/pmd85-emulator/README.md).

To work on the page, open `docs/index.html` in a browser.
