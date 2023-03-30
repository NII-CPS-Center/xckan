/**
 * CKANリソース(Extra)
 */
export interface Extra {
    key: string
    value: string
}

/**
 * CKANリソース。
 */
export interface Resource {
    id: string
    name: string
    description?: string
    url?: string
    format?: string
    created?: string
    last_modified?: string
}

/**
 * 組織情報。
 */
export interface Organization {
    image_url?: string
}

/**
 * データセット。
 */
export interface Dataset {
    /** ID。 */
    xckan_id: string
    /** タイトル。 */
    xckan_title: string
    /** サイト名。 */
    xckan_site_name: string
    /** サイトURL。 */
    xckan_site_url: string
    /** 最終更新日時(iso6801)。 */
    xckan_last_updated: string
    /** データセット種別。 */
    type: string
    /** 詳細説明。 */
    notes?: string
    /** Extras。 */
    extras: Extra[]
    /** リソースセット。 */
    resources: Resource[]
    /** 組織情報。 */
    organization?: Organization
    /** その他任意のプロパティ。 */
    [prop: string]: any
}

/** ファセット種別。  */
export type FacetKey = "organization" | "site" | "tag" | "format"

/**
 * ファセット。各属性の配列は、内容と個数の組を展開してそのまま連結したリスト。
 * > ["内容1", 個数1, "内容2", 個数2, ...]
 */
export interface Facet {
    /** 組織。 */
    organization: any[]
    /** サイト名。 */
    xckan_site_name: any[]
    /** タグ。 */
    tags: any[]
    /** ファイル形式。 */
    res_format: any[]
}

export function facets(values: any[]): [string, number][] {
    let m = new Array<[string, number]>()

    for (let i = 0; i < values.length; i+=2) {
        m.push([values[i] as string , values[i+1] as number])
    }

    return m
}