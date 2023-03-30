import { Module, VuexModule, Action, Mutation } from 'vuex-module-decorators'
import { Dataset, Facet, FacetKey } from '~/store/models'
import { Segment, parse, calculate } from '~/utils/leven'
import { $axios } from '~/utils/axios-accessor'

//----------------------------------------------------------------
// 検索関連データモデル。
//----------------------------------------------------------------
/** ソート項目。 */
export type SortType = "relevance" | "last_update"
/** 並び順。 */
export type SortOrder = "asc" | "desc"

export type QueryValues = {
    page: number
    limit: number
    sortType: SortType
    sortOrder: SortOrder
    keyword: string
    organizations: Array<string>
    sites: Array<string>
    tags: Array<string>
    formats: Array<string>
}

function cloneValues(values: QueryValues) {
    return {
        page: values.page,
        limit: values.limit,
        sortType: values.sortType,
        sortOrder: values.sortOrder,
        keyword: values.keyword,
        organizations: values.organizations.map(x => x),
        sites: values.sites.map(x => x),
        tags: values.tags.map(x => x),
        formats: values.formats.map(x => x),
    }
}

function parseFQ(fq: string, cont: (k: FacetKey, v: string) => any) {
    let sep = fq.indexOf(":")

    if (sep > 0) {
        cont(fq.slice(0, sep) as FacetKey, fq.slice(sep+1))
    }
}

/**
 * 検索クエリセット。
 */
export class Query {
    constructor(public values: QueryValues) {}

    static byQuery(params: object): Query {
        let query = defaultQuery()

        for (let [key, value] of Object.entries(params)) {
            switch (key) {
                case "q":
                    query.values.keyword = value
                    break
                case "fq":
                    if (value instanceof Array) {
                        (value as Array<string>).forEach(val => {
                            parseFQ(val, (k, v) => {
                                query.addFacet(k, v)
                            })
                        })
                    } else {
                        parseFQ(value, (k, v) => {
                            query.addFacet(k, v)
                        })
                    }
                    break
                case "sort":
                    query.values.sortType = value
                    break
                case "order":
                    query.values.sortOrder = value
                    break
                case "page":
                    let page = Number.parseInt(value)
                    if (page !== NaN) {
                        query.values.page = page
                    }
                case "limit":
                    let limit = Number.parseInt(value)
                    if (limit !== NaN) {
                        query.values.limit = limit
                    }
            }
        }

        return query
    }

    toQuery(): Record<string, string | string[]> {
        return {
            q: this.values.keyword,
            fq: this.values.organizations.map(v => `organization:${v}`)
                .concat(this.values.sites.map(v => `site:${v}`))
                .concat(this.values.tags.map(v => `tag:${v}`))
                .concat(this.values.formats.map(v => `format:${v}`)),
            sort: this.values.sortType,
            order: this.values.sortOrder,
            page: `${this.values.page}`,
            limit: `${this.values.limit}`,
        }
    }

    hasFacet(): boolean {
        return this.values.organizations.length > 0
            || this.values.sites.length > 0
            || this.values.tags.length > 0
            || this.values.formats.length > 0
    }

    addFacet(key: FacetKey, value: string) {
        switch (key) {
            case "organization":
                this.values.organizations = [value]
                //if (this.values.organizations.indexOf(value) < 0) {
                //    this.values.organizations.push(value)
                //}
                break
            case "site":
                this.values.sites = [value]
                //if (this.values.sites.indexOf(value) < 0) {
                //    this.values.sites.push(value)
                //}
                break
            case "tag":
                if (this.values.tags.indexOf(value) < 0) {
                    this.values.tags.push(value)
                }
                break
            case "format":
                if (this.values.formats.indexOf(value) < 0) {
                    this.values.formats.push(value)
                }
                break
        }
    }

    removeFacet(key: FacetKey, value: string) {
        switch (key) {
            case "organization":
                this.values.organizations = []
                //this.values.organizations = this.values.organizations.filter(x => x != value)
                break
            case "site":
                this.values.sites = []
                //this.values.sites = this.values.sites.filter(x => x != value)
                break
            case "tag":
                this.values.tags = this.values.tags.filter(x => x != value)
                break
            case "format":
                this.values.formats = this.values.formats.filter(x => x != value)
                break
        }
    }

    clearFacet() {
        this.values.organizations = []
        this.values.sites = []
        this.values.tags = []
        this.values.formats = []
    }

    get q(): string {
        return this.values.keyword || "*"
    }

    get fq(): string {
        return ([
            ["organization", this.values.organizations],
            ["xckan_site_name", this.values.sites],
            ["tags", this.values.tags],
            ["res_format", this.values.formats],
        ] as Array<[string, Array<string>]>)
            .filter(([_, vs]) => vs.length > 0)
            .map(([k, vs]) => `+${k}:${vs.map(x => `"${x}"`).join(" OR ")}`)
            .join(" ")
    }

    get sort(): string {
        let order: SortOrder = this.values.sortOrder == "desc" ? "desc" : "asc"

        switch (this.values.sortType) {
            case "relevance":
                return `score ${order}`
            case "last_update":
                return `xckan_last_updated ${order}`
            default:
                return `score ${order}`
        }
    }

    get start(): number {
        return (this.values.page - 1) * this.values.limit
    }

    get rows(): number { 
        return this.values.limit
    }
}

export function defaultQuery(): Query {
    return new Query({
        page: 1,
        limit: 50,
        sortType: "relevance",
        sortOrder: "desc",
        keyword: "",
        organizations: [],
        sites: [],
        tags: [],
        formats: [],
    })
}

/** 検索レスポンスの全体構造。 */
interface SearchResponse {
    result: {
        count: number
        facets: {
            facet_fields: Facet
        }
        q: {
            fq?: string
            q: string
            start: string
            rows: string
            sort: string
        }
        results: Dataset[]
    }
}

/** 検索処理の結果。 */
interface SearchResult {
    query: QueryValues
    response: SearchResponse
    receivedAt: Date
}

interface DatasetSeries {
    readonly entries: Array<Dataset>
    accept(another: Dataset): boolean
}

class SameSeries implements DatasetSeries {
    private id: string | null
    private name: string | null
    readonly entries: Array<Dataset>

    constructor(
        private dataset: Dataset,
    ) {
        this.entries = [dataset]
        this.id = dataset["id"] || null
        this.name = dataset["name"] || null
    }

    accept(another: Dataset): boolean {
        const anotherId: string | null = another["id"] || null
        const anotherName: string | null = another["name"] || null

        const ok = (this.id != null && this.id == anotherId) && (this.name != null && this.name == anotherName)

        if (ok) {
            this.entries.push(another)
        }

        return ok
    }
}

class SimilarSeries implements DatasetSeries {
    private host: string
    private threshold: number
    private segments: Array<Segment>
    readonly entries: Array<Dataset>

    constructor(
        private dataset: Dataset,
    ) {
        this.entries = [dataset]
        this.host = new URL(dataset.xckan_site_url).hostname
        this.threshold = 0

        this.segments = []
        parse(this.segments, dataset.xckan_title)
    }

    accept(another: Dataset): boolean {
        const anotherHost = new URL(another.xckan_site_url).hostname

        if (anotherHost != this.host) {
            return false
        }

        let anotherSegments: Array<Segment> = []
        parse(anotherSegments, another.xckan_title)

        const [ok, _] = calculate(this.segments, anotherSegments, this.threshold)

        if (ok) {
            this.entries.push(another)
        }

        return ok
    }
}

//----------------------------------------------------------------
// 取得関連データモデル。
//----------------------------------------------------------------
interface ShowResponse {
    result: Dataset
    success: Boolean
}

/** データセットストア。 */
@Module({
    name: "dataset",
    stateFactory: true,
    namespaced: true,
})
export default class DatasetStore extends VuexModule {
    /** 直近の取得結果。 */
    private _searchResult: SearchResult | null = null

    /** IDごとのデータセット。 */
    private _datasetMap: Map<string, Dataset> = new Map()

    /** 同一シリーズをまとめたデータセット。 */
    private _sameSeries: Array<Array<Dataset>> = []

    /** 類似シリーズをまとめたデータセット。 */
    private _similarSeries: Array<Array<Dataset>> = []

    /** 人気のタグ。 */
    private _hotTags: Array<[string, number]> | null = null

    /**
     * 最新の検索結果を取得する。
     */
    get datasets(): Dataset[] {
        return this._searchResult?.response.result.results ?? []
    }

    /**
     * 同一シリーズをまとめたデータセットを取得する。
     */
    get sameSeries(): Array<Array<Dataset>> {
        return this._sameSeries
    }

    /**
     * 類似シリーズをまとめたデータセットを取得する。
     */
    get similarSeries(): Array<Array<Dataset>> {
        return this._similarSeries
    }

    /**
     * 最新の検索結果のファセットを取得する。
     */
    get facets(): Facet {
        return this._searchResult?.response.result.facets.facet_fields ?? {
            organization: [],
            xckan_site_name: [],
            tags: [],
            res_format: [],
        }
    }

    /**
     * ファセット種別ごとの、最新の検索結果で利用した値を取得する。
     */
    get usedFacets(): Map<FacetKey, Array<string>> {
        let keys = new Map<FacetKey, Array<string>>()

        keys.set("organization", this._searchResult?.query.organizations ?? [])
        keys.set("site", this._searchResult?.query.sites ?? [])
        keys.set("tag", this._searchResult?.query.tags ?? [])
        keys.set("format", this._searchResult?.query.formats ?? [])

        return keys
    }

    /**
     * 最新の検索結果の総数を取得する。
     */
    get total(): number {
        return this._searchResult?.response.result.count ?? 0
    }

    /**
     * IDからデータセットを取得する関数を取得する。
     */
    get of(): (id: string) => (Dataset | null) {
        return id => this._datasetMap.get(id) ?? null
    }

    /**
     * 人気のタグを取得する。
     * @returns タグ文字列と個数の組のリスト。
     */
    get hotTags(): Array<[string, number]> {
        return this._hotTags ?? []
    }

    /**
     * 最新の検索クエリを取得する。
     */
    get query(): Query {
        return this._searchResult ? new Query(cloneValues(this._searchResult!.query)) : defaultQuery()
    }

    @Mutation
    setSearchResult(result: SearchResult) {
        let mapping = new Map<string, Dataset>()
        let sameSeries: Array<DatasetSeries> = []
        let similarSeries: Array<DatasetSeries> = []

        result.response.result.results.forEach(r => {
            mapping.set(r.xckan_id, r)

            // 同一結果をまとめる。
            let isSame = false

            for (let s of sameSeries) {
                if (s.accept(r)) {
                    isSame = true
                    break
                }
            }

            if (!isSame) {
                sameSeries.push(new SameSeries(r))
            }

            // 類似結果をまとめる。
            let segments: Array<Segment> = []
            parse(segments, r.xckan_title)

            let isSimilar = false

            for (let s of similarSeries) {
                if (s.accept(r)) {
                    isSimilar = true
                    break
                }
            }

            if (!isSimilar) {
                similarSeries.push(new SimilarSeries(r))
            }
        })

        this._datasetMap = mapping
        this._searchResult = result
        this._sameSeries = sameSeries.map(s => s.entries)
        this._similarSeries = similarSeries.map(s => s.entries)
    }

    @Mutation
    setDataset(dataset: Dataset) {
        let newMap = new Map<string, Dataset>()
        for (let [k, v] of this._datasetMap.entries()) {
            newMap.set(k, v)
        }
        newMap.set(dataset.xckan_id, dataset)
        this._datasetMap = newMap
        //this._datasetMap.set(dataset.xckan_id, dataset)
    }

    @Mutation
    setHotTags(tags: Array<[string, number]>) {
        this._hotTags = tags
    }

    /**
     * データセット検索を行う。
     * @param params 検索クエリと、常に取り直すフラグを持つオブジェクト。
     */
    @Action
    async search(params: {
        query: Query
        reload?: boolean
    }): Promise<void> {
        if (this._searchResult === null || (params.reload ?? false)) {
            let r = await $axios.get<SearchResponse>('/package_search', {
                params: {
                    q: params.query.q,
                    fq: params.query.fq || undefined,
                    start: params.query.start,
                    rows: params.query.rows,
                    sort: params.query.sort,
                }
            })

            this.setSearchResult({
                query: params.query.values,
                response: r.data,
                receivedAt: new Date(),
            })
        }
    }

    /**
     * IDにより単一のデータセット取得する。
     * @param params データセットのIDと、常に取り直すフラグを持つオブジェクト。
     */
    @Action
    async fetch(params: {
        id: string
        reload?: boolean
    }): Promise<any> {
        if (!this._datasetMap.has(params.id) || (params.reload ?? false)) {
            try {
                let r = await $axios.get<ShowResponse>('/package_show', {
                    params: { id: params.id }
                })
                if(r.data && r.data.success) {
                    this.setDataset(r.data.result)
                    return r.data.result    
                } else {
                    return null
                }
            } catch(e) {
                console.log(`error: ${e}`)
            }
        } else {
            return this._datasetMap.get(params.id)
        }
    }

    /**
     * 人気のタグを全て取得する。
     * @param params 常に取り直すフラグを持つオブジェクト。
     */
    @Action
    async fetchHotTags(params?: {
        reload?: boolean
    }): Promise<void> {
        if (!this._hotTags || (params?.reload ?? false)) {
            let r = await $axios.get<object>('/hot_tag')

            this.setHotTags(Object.entries(r.data).map(([tag, count]) => [tag, count as number]))
        }
    }
}