import { parse, calculate, Segment } from '~/utils/leven'

function compare(v1: string, v2: string, output: boolean=false) {
    let seg1: Array<Segment> = []
    let seg2: Array<Segment> = []

    parse(seg1, v1)
    parse(seg2, v2)

    if (output) {
        console.log(`y: ${seg1.map(s => s.value).join()}`)
        console.log(`x: ${seg2.map(s => s.value).join()}`)
    }

    let [status, matrix] = calculate(seg1, seg2, 0)

    if (output) {
        let log = []
        for (let row of matrix) {
            let line = ""
            for (let d of row) {
                if (d < 100) {
                    line += ' '
                    if (d < 10) {
                        line += ' '
                    }
                }
                line += ` ${d}`
            }
            log.push(line)
        }
        console.log(log.join("\n"))
    }

    return status
}

describe("parse-title", () => {
    test("同じ文字列は一致", () => {
        expect(compare(
            "平成30年静岡",
            "平成30年静岡",
        )).toBeTruthy()
    })

    test("数値", () => {
        expect(compare(
            "平成30年静岡",
            "平成31年静岡",
        )).toBeTruthy()
    })

    test("年号", () => {
        expect(compare(
            "平成30年静岡",
            "昭和31年静岡",
        )).toBeTruthy()
    })

    test("未定義文字列の不一致", () => {
        expect(compare(
            "平成30年静岡",
            "昭和31年東京",
        )).toBeFalsy()
    })

    test("元年", () => {
        expect(compare(
            "平成元年静岡",
            "昭和31年静岡",
        )).toBeTruthy()
    })

    test("年号アルファベット", () => {
        expect(compare(
            "H30年静岡",
            "S31年静岡",
        )).toBeTruthy()
    })

    test("文脈依存をxに指定", () => {
        expect(compare(
            "昭和31年静岡",
            "平成元年静岡",
        )).toBeTruthy()
    })

    test("片方が長い", () => {
        expect(compare(
            "昭和31年静岡県静岡市",
            "昭和31年静岡",
            true,
        )).toBeFalsy()
    })
})