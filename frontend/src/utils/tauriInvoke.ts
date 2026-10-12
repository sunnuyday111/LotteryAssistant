/** 调用 Tauri 2 IPC 命令的轻量封装（不依赖 @tauri-apps/api 包）。 */

export async function invoke<T = unknown>(
  cmd: string,
  args: Record<string, unknown> = {},
): Promise<T> {
  const w = window as unknown as {
    __TAURI_INTERNALS__?: {
      invoke: (cmd: string, args: unknown) => Promise<unknown>
    }
  }
  if (!w.__TAURI_INTERNALS__?.invoke) {
    throw new Error('Tauri IPC 不可用（仅在桌面端可用）')
  }
  return (await w.__TAURI_INTERNALS__.invoke(cmd, args)) as T
}