//----------------------------------------------------------------
// 共通型・関数。
//----------------------------------------------------------------
/**
 * 距離計算単位となる部分文字列と持ち、定義された距離計算を適用する文字列セグメント。
 */
export interface Segment {
    /** 部分文字列。 */
    readonly value: string
    /** 前のセグメント。 */
    prev: Segment | null
    /** 次のセグメント。 */
    next: Segment | null

    /**
     * 別のセグメントとの距離を計算し、距離マトリクスを埋める。
     * @param data Levenshtein距離マトリクス。
     * @param y y軸始点。
     * @param x x軸始点。
     * @param other 距離計算対象のセグメント。
     * @param threshold 距離閾値以下の外接点の現在数と距離閾値の組。
     * @returns 処理継続フラグ。閾値以下の外接点が無くなった時にfalseを返す。
     */
    calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean

    /**
     * 指定した型のセグメントに変換する。
     * @param t セグメントの型。
     * @returns 型の変換されたセグメント。対応しない型の場合null。
     */
    asSegment<T extends Segment>(t: new(...args: any) => T): T | null
}

/**
 * 文字列の先頭から適切なセグメントを切り出す機能を定義するインタフェース。
 * 
 * Segment実装クラスと対応するConsumerとして、適切な条件を満たす場合にそのセグメントを生成するように実装する。
 */
interface Consumer {
    /**
     * 文字列の先頭から適切なセグメントを生成する。
     * @param value 対象文字列。
     * @param prev 前のセグメント。
     * @returns 生成されたセグメント。文字列が条件を満たさずに、セグメントを生成しなかった場合はnull。
     */
    consume(value: string, prev: Segment | null): Segment | null
}

/**
 * 共通プロパティを定義したセグメント抽象基底クラス。
 */
abstract class SegmentBase implements Segment {
    constructor(
        readonly value: string,
        public prev: Segment | null,
        public next: Segment | null,
    ) {
        if (prev) {
            prev.next = this
        }
    }

    abstract calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean

    asSegment<T extends Segment>(t: new(...args: any) => T): T | null {
        return this instanceof t ? this : null
    }
}

/**
 * 距離マトリクスの指定した範囲の値を埋める。
 * @param data Levenshtein距離マトリクス。
 * @param ys y軸文字列。
 * @param xs x軸文字列。
 * @param sy y軸始点。
 * @param sx x軸始点。
 * @param threshold 距離閾値以下の外接点の現在数と距離閾値の組。
 * @param replaceCost 範囲全体の固定置換コスト。
 * @returns 処理継続フラグ。閾値以下の外接点が無くなった時にfalseを返す。
 */
function setCosts(data: number[][], ys: string, xs: string, sy: number, sx: number, threshold: [number, number], replaceCost?: number): boolean {
    let fixedCost = (typeof replaceCost == "number" ? replaceCost + data[sy-1][sx-1] : undefined)

    for (let iy=0; iy<ys.length; iy++) {
        let y = sy + iy
        for (let ix=0; ix<xs.length; ix++) {
            let x = sx + ix
            let ins = data[y][x-1] + 1
            let del = data[y-1][x] + 1
            let rep = fixedCost ?? data[y-1][x-1] + (ys[iy] == xs[ix] ? 0 : 1)
            let cost = Math.min(ins, del, rep)
            data[y][x] = cost
            if (cost > threshold[1]) {
                if (data[y-1][x-1] <= threshold[1]) {
                    threshold[0]--
                }
                if (x == data[y-1].length-1 && data[y-1][x] <= threshold[1]) {
                    threshold[0]--
                }
                if (y == data.length-1 && data[y][x-1] <= threshold[1]) {
                    threshold[0]--
                }

                if (threshold[0] <= 0) {
                    return false
                }
            } else if (cost <= threshold[1] && data[y-1][x-1] > threshold[1]) {
                threshold[0]++
            }
        }
    }
    return true
}

//----------------------------------------------------------------
// 文字セグメント。
// 単純な文字対応のLeveshtein距離計算を行う。
//----------------------------------------------------------------
class CharacterSegment extends SegmentBase {
    length(): number {
        return 1
    }

    calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean {
        return setCosts(data, this.value, other.value, y, x, threshold)
    }
}

const CharacterConsumer: Consumer = {
    consume(value: string, prev: Segment | null): Segment | null {
        return new CharacterSegment(value[0], prev, null)
    }
}

//----------------------------------------------------------------
// 単語セグメント。
// 同一カテゴリの単語セグメントとの距離を0と見なす。
//----------------------------------------------------------------
enum WordCategory {
    era,
    eraAlphabet,
}

class WordSegment extends SegmentBase {
    constructor(
        value: string,
        prev: Segment | null,
        readonly category: WordCategory,
    ) {
        super(value, prev, null)
    }

    calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean {
        let word = other.asSegment(WordSegment)

        if (word && this.category == word.category) {
            return setCosts(data, this.value, word.value, y, x, threshold, 0)
        } else {
            return setCosts(data, this.value, other.value, y, x, threshold)
        }
    }
}

class WordConsumer implements Consumer {
    constructor(
        readonly category: WordCategory,
        readonly words: Array<string>,
    ) {}

    consume(value: string, prev: Segment | null): Segment | null {
        let match = this.words.find(w => value.startsWith(w))
        return match ? new WordSegment(match, prev, this.category) : null
    }
}

//----------------------------------------------------------------
// 数値セグメント。
// 数値セグメント同士の距離を0と見なす。
//----------------------------------------------------------------
const digitCharacters = new Set("0123456789０１２３４５６７８９")

class DigitSegment extends SegmentBase {
    calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean {
        let digit = other.asSegment(DigitSegment)

        if (digit) {
            return setCosts(data, this.value, digit.value, y, x, threshold, 0)
        } else {
            return setCosts(data, this.value, other.value, y, x, threshold)
        }
    }
}

const DigitConsumer: Consumer = {
    consume(value: string, prev: Segment | null): Segment | null {
        let index = 0
        for (let c of value) {
            if (digitCharacters.has(c)) {
                index++
            } else {
                break
            }
        }
        return index > 0 ? new DigitSegment(value.slice(0, index), prev, null) : null
    }
}

//----------------------------------------------------------------
// 括弧セグメント。
//----------------------------------------------------------------
class BracketSegment extends SegmentBase {
    constructor(
        value: string,
        prev: Segment | null,
        readonly bracket: [string, string],
        readonly children: Array<Segment>,
    ) {
        super(value, prev, null)
    }

    calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean {
        let bracket = other.asSegment(BracketSegment)

        if (bracket) {
            for (let c of this.children) {
                for (let d of bracket.children) {
                    if (!c.calculate(data, y, x, d, threshold)) {
                        return false
                    }
                    x += d.value.length
                }
                y += c.value.length
            }
            return true
        } else {
            return setCosts(data, this.value, other.value, y, x, threshold)
        }
    }
}

const bracketCharacters: Array<[Set<string>, Set<string>]> = [
    [new Set("("), new Set(")")],
]

const BracketConsumer: Consumer = {
    consume(value: string, prev: Segment | null): Segment | null {
        if (value.length < 2) {
            return null
        }

        let bracket = bracketCharacters.find(bc => bc[0].has(value[0]))

        if (bracket) {
            let segments: Array<Segment> = []

            let consumed = parse(segments, value.slice(1), s => bracket!![1].has(s))

            if (value[consumed+1]) {
                return new BracketSegment(value.slice(0, consumed+2), prev, [value[0], value[consumed+1]], segments)
            } else {
                return new BracketSegment(value.slice(0, consumed+1), prev, [value[0], ""], segments)
            }
        } else {
            return null
        }
    }
}

//----------------------------------------------------------------
// 文脈依存セグメント。
// 前後関係により、異なる種別のセグメントとして振る舞う。
//----------------------------------------------------------------
class ContextualSegment extends SegmentBase {
    constructor(
        value: string,
        prev: Segment | null,
        readonly key: string,
        private converter: (cxt: ContextualSegment) => Segment | null,
    ) {
        super(value, prev, null)
    }

    calculate(data: number[][], y: number, x: number, other: Segment, threshold: [number, number]): boolean {
        let contextual = this.converter(this)

        if (contextual) {
            return contextual.calculate(data, y, x, other, threshold)
        } else {
            return setCosts(data, this.value, other.value, y, x, threshold)
        }
    }

    asSegment<T extends Segment>(t: new(...args: any) => T): T | null {
        let contextual = this.converter(this)

        return contextual instanceof t ? contextual : null
    }
}

class ContextualConsumer implements Consumer {
    constructor(
        readonly key: string,
        readonly words: Array<string>,
        private converter: (cxt: ContextualSegment) => Segment | null,
    ) {}

    consume(value: string, prev: Segment | null): Segment | null {
        let match = this.words.find(w => value.startsWith(w))
        return match ? new ContextualSegment(match, prev, this.key, this.converter) : null
    }
}

function year1(cxt: ContextualSegment): Segment | null {
    if (cxt.prev instanceof WordSegment) {
        if (cxt.prev.category == WordCategory.era) {
            return new DigitSegment(cxt.value, cxt.prev, cxt.next)
        }
    }

    return null
}

function eraAlphabet(cxt: ContextualSegment): Segment | null {
    let maybeYear = cxt.next

    if (maybeYear instanceof CharacterSegment) {
        if (maybeYear.value == ".") {
            maybeYear = maybeYear.next
        }
    }

    if (maybeYear instanceof DigitSegment) {
        if (maybeYear.value.length <= 2) {
            return new WordSegment(cxt.value, cxt.prev, WordCategory.eraAlphabet)
        }
    }

    return null
}

//----------------------------------------------------------------
// 距離計算API。
//----------------------------------------------------------------
/**
 * 適用順に並べられたConsumerリスト。CharacterConsumerを必ず最後の要素とする。
 */
const consumers: Array<Consumer> = [
    new WordConsumer(WordCategory.era, ["昭和", "平成", "令和"]),
    new ContextualConsumer("year1", ["元"], year1),
    new ContextualConsumer("eraAlphabet", ["S", "H", "R", "Ｓ", "Ｈ", "Ｒ"], eraAlphabet),
    BracketConsumer,
    DigitConsumer,
    CharacterConsumer,
]

/**
 * 文字列をパーズして、セグメントをリストに格納する。
 * @param segments セグメント格納リスト。関数実行により、セグメントが追加される。
 * @param value パーズする文字列。
 * @param eos パーズ終了条件。デフォルトは全ての文字を読み込んだ時点で終了する。
 * @returns パーズを行った文字数。
 */
export function parse(segments: Array<Segment>, value: string, eos?: (s: string) => boolean): number {
    if (value == "" || eos?.(value[0])) {
        return 0
    }

    for (let c of consumers) {
        let seg = c.consume(value, segments[segments.length-1] ?? null)

        if (seg) {
            segments.push(seg)

            let consumed = seg.value.length

            return consumed + parse(segments, value.slice(consumed), eos)
        }
    }

    throw `No consumer accept input ${value}`
}

/**
 * 二つのセグメントリスト間の距離が、ある値以下に収まるか調べる。
 * @param segments1 y軸に設定されるセグメントリスト。
 * @param segments2 x軸に設定されるセグメントリスト。
 * @param maximumCost 許容される最大距離。
 * @returns セグメント間の距離が指定した最大値以下に収まったかを示す真偽値と、計算終了時点のLevenshtein距離マトリクス。
 */
export function calculate(segments1: Array<Segment>, segments2: Array<Segment>, maximumCost: number): [boolean, number[][]] {
    let ylen = segments1.map(s => s.value.length).reduce((acc, x) => acc+x, 0)
    let xlen = segments2.map(s => s.value.length).reduce((acc, x) => acc+x, 0)

    let data: number[][] = Array(ylen+1)
    for (let y=0; y<ylen+1; y++) {
        data[y] = Array(xlen+1)
        for (let x=0; x<xlen+1; x++) {
            data[y][x] = (y == 0 ? x : (x == 0 ? y : 0))
        }
    }

    let threshold = [maximumCost * 2 + 1, maximumCost] as [number, number]

    let y = 1
    for (let s1 of segments1) {
        let x = 1
        for (let s2 of segments2) {
            if(!s1.calculate(data, y, x, s2, threshold)) {
                return [false, data]
            }
            x += s2.value.length
        }
        y += s1.value.length
    }

    return [true, data]
}