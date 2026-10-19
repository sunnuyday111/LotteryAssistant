#!/usr/bin/env node
/**
 * 用最新 git tag 同步各处版本号。
 *
 * 版本号散落在 5 个文件里，漏改任何一个都会让安装包文件名、Windows 程序属性
 * 或 Cargo 包版本对不上——历史上就是这么从 v0.1.0 一路漂到 v0.1.2 的。
 * 构建前统一跑一次，从根上消除漂移。
 *
 * 用法：
 *   node scripts/sync-version.mjs          # 改写文件
 *   node scripts/sync-version.mjs --check  # 只校验，不一致时以退出码 1 结束
 *
 * 版本取值优先级：
 *   1. 环境变量 RELEASE_VERSION（CI 或特殊构建显式指定）
 *   2. git describe --tags --abbrev=0 —— HEAD 可达的最新 tag
 *   3. 保持 tauri.conf.json 里的现值并告警（仓库还没有任何 tag 时）
 */

import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const checkOnly = process.argv.includes('--check')

/** 宽松的 semver：1.2.3 或 1.2.3-rc.1 */
const VERSION_RE = /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)*$/

/** 取 HEAD 可达的最新 tag，去掉前缀 v。取不到返回 null。 */
function versionFromGit() {
  try {
    const out = execFileSync('git', ['describe', '--tags', '--abbrev=0'], {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
    return out.replace(/^v/, '')
  } catch (err) {
    // 常见原因：仓库还没有 tag、CI 浅克隆（需 fetch-depth: 0）、git 不可用
    const reason = String(err.message ?? err).split('\n')[0]
    console.warn(`[sync-version] git describe 未取到版本（${reason}）`)
    return null
  }
}

const TAURI_CONF = join(root, 'desktop', 'src-tauri', 'tauri.conf.json')
const CARGO_TOML = join(root, 'desktop', 'src-tauri', 'Cargo.toml')
const CARGO_LOCK = join(root, 'desktop', 'src-tauri', 'Cargo.lock')
const DESKTOP_PKG = join(root, 'desktop', 'package.json')
const FRONTEND_PKG = join(root, 'frontend', 'package.json')

/** tauri.conf.json 的 version 是安装包文件名的唯一来源，也是本次的基准。 */
function currentVersion() {
  if (!existsSync(TAURI_CONF)) return null
  const match = readFileSync(TAURI_CONF, 'utf8').match(/"version"\s*:\s*"([^"]*)"/)
  return match ? match[1] : null
}

function resolveVersion() {
  const fromEnv = (process.env.RELEASE_VERSION || '').trim().replace(/^v/, '')
  const fromGit = versionFromGit()

  for (const [source, value] of [
    ['RELEASE_VERSION', fromEnv],
    ['git tag', fromGit],
  ]) {
    if (!value) continue
    if (!VERSION_RE.test(value)) {
      console.error(`[sync-version] ${source} 给出的 "${value}" 不是合法版本号，已中止。`)
      process.exit(1)
    }
    console.log(`[sync-version] 版本来源：${source} → ${value}`)
    return value
  }

  const fallback = currentVersion()
  if (fallback) {
    console.warn(`[sync-version] 未找到可用的 git tag，保持 tauri.conf.json 中的 ${fallback}。`)
    return fallback
  }
  console.error('[sync-version] 既没有 RELEASE_VERSION、没有 git tag，也读不到当前版本。')
  process.exit(1)
}

/** 读文件、对内容做一次替换，返回是否发生了变化。 */
function patch(file, transform) {
  if (!existsSync(file)) {
    console.warn(`[sync-version] 跳过不存在的文件：${file}`)
    return false
  }
  const before = readFileSync(file, 'utf8')
  const after = transform(before)
  if (after === before) return false
  if (!checkOnly) writeFileSync(file, after, 'utf8')
  return true
}

/** 只替换第一个匹配，避免误伤同名字段。 */
function replaceFirst(content, re, replacement) {
  return content.replace(re, replacement)
}

/** package.json 走 JSON 解析，保证只改 version、不动其他内容与格式。 */
function patchPackageJson(file, version) {
  if (!existsSync(file)) {
    console.warn(`[sync-version] 跳过不存在的文件：${file}`)
    return false
  }
  const before = readFileSync(file, 'utf8')
  const data = JSON.parse(before)
  if (data.version === version) return false
  data.version = version
  const after = JSON.stringify(data, null, 2) + '\n'
  if (!checkOnly) writeFileSync(file, after, 'utf8')
  return true
}

const version = resolveVersion()

const changes = [
  ['desktop/src-tauri/tauri.conf.json',
    patch(TAURI_CONF, (c) => replaceFirst(c, /("version"\s*:\s*")[^"]*(")/, `$1${version}$2`))],

  ['desktop/src-tauri/Cargo.toml',
    patch(CARGO_TOML, (c) => {
      // 只改 [package] 段里的版本，避免动到依赖声明
      const at = c.indexOf('[package]')
      if (at < 0) return c
      const head = c.slice(0, at)
      const tail = c.slice(at).replace(/^version\s*=\s*"[^"]*"/m, `version = "${version}"`)
      return head + tail
    })],

  ['desktop/src-tauri/Cargo.lock',
    patch(CARGO_LOCK, (c) =>
      replaceFirst(c, /(name = "lottery-assistant"\nversion = ")[^"]*(")/, `$1${version}$2`))],

  ['desktop/package.json', patchPackageJson(DESKTOP_PKG, version)],
  ['frontend/package.json', patchPackageJson(FRONTEND_PKG, version)],
]

const touched = changes.filter(([, changed]) => changed).map(([name]) => name)

if (touched.length === 0) {
  console.log(`[sync-version] 各处版本号已是 ${version}，无需改动。`)
} else if (checkOnly) {
  console.error(`[sync-version] --check 失败，以下文件与 ${version} 不一致：\n  ${touched.join('\n  ')}`)
  process.exit(1)
} else {
  console.log(`[sync-version] 已更新为 ${version}：\n  ${touched.join('\n  ')}`)
}
