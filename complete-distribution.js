#!/usr/bin/env node
/**
 * Fabric Loader jar + Version Manifest(json)를 공식 서버에서 내려받아
 * loader/ 폴더에 저장하고, MD5/size를 loader/loader-info.json에 기록합니다.
 *
 * 이 컴퓨터(사용자 PC)는 인터넷이 되므로 여기서 실행하세요.
 * Claude가 만든 샌드박스에는 외부 인터넷 접근이 없어서 이 파일들은
 * 미리 받아둘 수 없었습니다. 아래 순서대로 실행하면 자동 완성됩니다.
 *
 * 사용법:
 *   1) node complete-distribution.js       (loader 파일 다운로드 + 해시 계산)
 *   2) python3 generate_distribution.py    (distribution.json에 해시 반영)
 *
 * 또는 둘 다 순서대로 실행해주는 `node build-all.js`를 사용하세요.
 */
const fs = require('fs')
const path = require('path')
const crypto = require('crypto')
const https = require('https')

const MC_VERSION = '1.21.4'
const FABRIC_LOADER_VERSION = '0.19.3'
const FABRIC_VERSION_ID = `fabric-loader-${FABRIC_LOADER_VERSION}-${MC_VERSION}`

const LOADER_JAR_URL = `https://maven.fabricmc.net/net/fabricmc/fabric-loader/${FABRIC_LOADER_VERSION}/fabric-loader-${FABRIC_LOADER_VERSION}.jar`
const PROFILE_JSON_URL = `https://meta.fabricmc.net/v2/versions/loader/${MC_VERSION}/${FABRIC_LOADER_VERSION}/profile/json`
const INTERMEDIARY_URL = `https://maven.fabricmc.net/net/fabricmc/intermediary/${MC_VERSION}/intermediary-${MC_VERSION}.jar`

const LOADER_DIR = path.join(__dirname, 'loader')
const LOADER_JAR_PATH = path.join(LOADER_DIR, `fabric-loader-${FABRIC_LOADER_VERSION}.jar`)
const MANIFEST_PATH = path.join(LOADER_DIR, `${FABRIC_VERSION_ID}.json`)
const INTERMEDIARY_PATH = path.join(LOADER_DIR, `intermediary-${MC_VERSION}.jar`)
const INFO_PATH = path.join(LOADER_DIR, 'loader-info.json')

function download(url, destPath) {
    return new Promise((resolve, reject) => {
        const file = fs.createWriteStream(destPath)
        https.get(url, { headers: { 'User-Agent': 'hanwol-distribution-builder' } }, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                file.close()
                fs.unlinkSync(destPath)
                return resolve(download(res.headers.location, destPath))
            }
            if (res.statusCode !== 200) {
                file.close()
                return reject(new Error(`다운로드 실패 (${res.statusCode}): ${url}`))
            }
            res.pipe(file)
            file.on('finish', () => file.close(resolve))
        }).on('error', reject)
    })
}

function md5AndSize(filePath) {
    const buf = fs.readFileSync(filePath)
    const md5 = crypto.createHash('md5').update(buf).digest('hex')
    return { md5, size: buf.length }
}

async function main() {
    fs.mkdirSync(LOADER_DIR, { recursive: true })

    console.log(`[1/3] Fabric Loader jar 다운로드 중...\n  ${LOADER_JAR_URL}`)
    await download(LOADER_JAR_URL, LOADER_JAR_PATH)

    console.log(`[2/3] Version Manifest(json) 다운로드 중...\n  ${PROFILE_JSON_URL}`)
    await download(PROFILE_JSON_URL, MANIFEST_PATH)

    console.log(`[3/3] Intermediary jar 다운로드 중... (해시가 API에 없어서 직접 계산)\n  ${INTERMEDIARY_URL}`)
    await download(INTERMEDIARY_URL, INTERMEDIARY_PATH)

    const loaderHash = md5AndSize(LOADER_JAR_PATH)
    const manifestHash = md5AndSize(MANIFEST_PATH)
    const intermediaryHash = md5AndSize(INTERMEDIARY_PATH)

    const info = {
        loaderMD5: loaderHash.md5,
        loaderSize: loaderHash.size,
        manifestMD5: manifestHash.md5,
        manifestSize: manifestHash.size,
        intermediaryMD5: intermediaryHash.md5,
        intermediarySize: intermediaryHash.size,
    }
    fs.writeFileSync(INFO_PATH, JSON.stringify(info, null, 2))

    console.log('\n완료! loader/loader-info.json 에 해시가 저장되었습니다:')
    console.log(info)
    console.log('\n다음 단계: python3 generate_distribution.py 를 실행해서 distribution.json에 반영하세요.')
    console.log('(intermediary-*.jar은 GitHub에 올릴 필요 없음 - distribution.json이 maven.fabricmc.net을 직접 가리킵니다)')
}

main().catch((err) => {
    console.error('에러:', err.message)
    process.exit(1)
})
