import fsd from "@feature-sliced/steiger-plugin"
import { defineConfig } from "steiger"

// Steiger uses Chokidar even for a one-shot scan. Polling also works in sandboxed environments.
process.env.CHOKIDAR_USEPOLLING ??= "1"

export default defineConfig(fsd.configs.recommended)
