<template>
    <div>
        <section id="search" class="search">
            <div class="search__inner">
                <div class="search__form">
                    <form id="top__search__form" action="" v-on:submit.prevent.stop="search">
                        <input v-model="query.values.keyword"
                            id="search__box" class="search__box" name="search__box" type="text" placeholder="データセットを検索" />
                        <button class="search__btn" aria-label="検索" type="button" @click="search">
                            <i class="fas fa-search"></i>
                        </button>
                    </form>
                </div>
            </div>
        </section>

        <section id="result-head" class="result-head">
            <div class="result-head__inner">
                <div class="result-head__message"><span>{{ total }}</span>件のデータが見つかりました​</div>
                <div class="result-head__sort">
                    <div class="result-head__sort__item">
                    <select v-model="query.values.sortType" v-on:change="search">
                        <option value="relevance">関連度の高い順</option>
                        <option value="last_update">更新日</option>
                    </select>
                    </div>
                    <div class="result-head__sort__item">
                    <select v-model="query.values.limit" v-on:change="search">
                        <option value="50">50件</option>
                        <option value="100">100件</option>
                        <option value="200">200件</option>
                        <option value="500">500件</option>
                    </select>
                    </div>
                </div>
            </div>
      </section>

      <section class="result-aggregate">
           <div class="switch">
               <input id="no-aggregate" type="radio" class="agg-select" name="agg-select" value="no" v-model="aggregationType" />
               <label for="no-aggregate">個別表示</label>&nbsp;
               <input id="similar-aggregate" type="radio" class="agg-select" name="agg-select" value="similar" v-model="aggregationType" />
               <label for="similar-aggregate">シリーズをグループ化</label>&nbsp;
               <input id="same-aggregate" type="radio" class="agg-select" name="agg-select" value="same" v-model="aggregationType" />
               <label for="same-aggregate">重複結果をグループ化</label>&nbsp;
           </div>
      </section>

      <div class="content content-has-column">
            <FacetMenu :facet="facet"
                v-on:add-facet="addFacet"
                v-on:remove-facet="removeFacet"
                v-on:clear-facet="clearFacet" />
            <main class="content__main">
                <ul class="filtered">
                    <li v-for="kv in usedFacets" :key="`${kv[0]}_${kv[1]}`" class="filtered__item">{{ kv[1] }}
                        <a href="#" class="filtered__remove" title="削除"
                            @click="removeFacet(kv[0], kv[1])"><i class="fas fa-times"></i></a>
                    </li>
                </ul>
                <ul class="result">
                    <template v-if="aggregationType == 'similar'">
                        <template v-for="(ds, index) in similarSeries">
                            <DatasetItem :dataset="ds[0]" :aggregation="ds.length > 1" :key="`${ds[0].xckan_id}_series`"
                                v-on:show-aggregation="showAggregation(index)" />
                        </template>
                    </template>
                    <template v-else-if="aggregationType == 'same'">
                        <template v-for="(ds, index) in sameSeries">
                            <DatasetItem :dataset="ds[0]" :aggregation="ds.length > 1" :key="`${ds[0].xckan_id}_series`"
                                v-on:show-aggregation="showAggregation(index)" />
                        </template>
                    </template>
                    <template v-else>
                        <DatasetItem v-for="(d, index) in datasets" :key="`${d.xckan_id}_${index}`" :dataset="d" />
                    </template>
                </ul>

                <nav class="pager">
                    <ul class="pager__inner">
                        <li v-for="p in pager" :key="p[0]" class="pager__item">
                            <a class="pager__link" :class="{ pager__link__active: p[2] }" href="" @click.prevent.stop="changePage(p[1])">
                                <template v-if="p[0] == '<<'"><i class="fas fa-angle-double-left"></i></template>
                                <template v-else-if="p[0] == '<'"><i class="fas fa-angle-left"></i></template>
                                <template v-else-if="p[0] == '>'"><i class="fas fa-angle-right"></i></template>
                                <template v-else-if="p[0] == '>>'"><i class="fas fa-angle-double-right"></i></template>
                                <template v-else>{{ p[0] }}</template>
                            </a>
                        </li>
                    </ul>
                </nav>
          </main>
      </div>

      <div v-show="aggregationIndex !== null" class="modal-bg">
          <div class="modal-container">
              <div class="modal-header">
                  <div class="title">{{ selectedSeries.title }}</div>
                  <a href="" class="close" @click.prevent.stop="hideAggregation">×</a>
              </div>
              <div class="modal-content">
                <ul class="result">
                    <DatasetItem v-for="(d, index) in selectedSeries.children" :key="`${d.xckan_id}_${index}`" :dataset="d" />
                </ul>
              </div>
          </div>
      </div>

    </div>

</template>

<script lang="ts">
import { Vue, Component } from 'nuxt-property-decorator'
import { Route } from 'vue-router'
import DatasetItem from '~/components/dataset-item.vue'
import FacetMenu from '~/components/facet.vue'
import { datasetStore } from '~/store'
import { Query, defaultQuery } from '~/store/dataset'
import { Dataset, Facet, FacetKey } from '~/store/models'
import { disableBodyScroll, clearAllBodyScrollLocks } from 'body-scroll-lock'

type PageItem = "<<" | "<" | number | ">" | ">>"
type AggregationType = "no" | "same" | "similar"

class Series {
    constructor(
        private datasets: Array<Dataset>
    ) {}

    get title(): string {
        return this.datasets.length > 0 ? this.datasets[0].xckan_title : ""
    }

    get children(): Array<Dataset> {
        return this.datasets.slice(1)
    }
}

@Component({
    components: { DatasetItem, FacetMenu },
})
export default class IndexPage extends Vue {
    //query!: Query

    enabled: Boolean = false

    aggregationType: AggregationType = "no"

    aggregationIndex: number | null = null

    get datasets(): Dataset[] {
        return datasetStore.datasets
    }

    get similarSeries(): Array<Array<Dataset>> {
        return datasetStore.similarSeries
    }

    get sameSeries(): Array<Array<Dataset>> {
        return datasetStore.sameSeries
    }

    get selectedSeries(): Series {
        if (this.aggregationIndex != null) {
            if (this.aggregationType == "similar") {
                return new Series(this.similarSeries[this.aggregationIndex])
            } else if (this.aggregationType == "same") {
                return new Series(this.sameSeries[this.aggregationIndex])
            }
        }
        return new Series([])
    }

    get facet(): Facet {
        return datasetStore.facets
    }

    get total(): number {
        return datasetStore.total
    }

    get usedFacets(): Array<[FacetKey, string]> {
        let facets: Array<[FacetKey, string]> = []

        for (let [k, values] of datasetStore.usedFacets.entries()) {
            for (const v of values) {
                facets.push([k, v])
            }
        }

        return facets
    }

    get query(): Query {
        return datasetStore.query
    }

    get hotTags(): Array<[string, number]> {
        return datasetStore.hotTags
    }

    get pager(): Array<[PageItem, number, boolean]> {
        let current = this.query.values.page
        let limit = this.query.values.limit
        let total = datasetStore.total
        let length = 10
        let lhs = Math.floor((length - 1) / 2)
        let rhs = length - 1 - lhs

        let pages: Array<[PageItem, number, boolean]> = []

        let maxPage = Math.floor(total / limit) + (total % limit == 0 ? 0 : 1)

        if (maxPage <= 1) {
            return []
        }

        if (current - lhs >= 3) {
            pages.push(["<<", 1, false])
        }
        if (current - lhs >= 2) {
            pages.push(["<", current - 1, false])
        }

        let begin = Math.max(1, current - lhs)
        let end = Math.min(maxPage, current + rhs)

        for (let p = begin; p <= end; p++) {
            pages.push([p, p, p == current])
        }

        if (maxPage - (current + rhs) >= 1) {
            pages.push([">", current + 1, false])
        }
        if (maxPage - (current + rhs) >= 2) {
            pages.push([">>", maxPage, false])
        }

        return pages
    }

    private moveForSearch(q: Query) {
        this.$router.push({
            path: "/",
            query: q.toQuery(),
        })
    }
    
    private executeSearch(r: Route) {
        let q = Query.byQuery(r.query)

        datasetStore.search({
            query: q,
            reload: true,
        })
    }

    search() {
        this.query.values.page = 1
        this.moveForSearch(this.query)
    }

    addFacet(key: FacetKey, value: string) {
        this.query.addFacet(key, value)
        this.moveForSearch(this.query)
    }

    removeFacet(key: FacetKey, value: string) {
        this.query.removeFacet(key, value)
        this.moveForSearch(this.query)
    }

    clearFacet() {
        if (this.query.hasFacet()) {
            this.query.clearFacet()
            this.moveForSearch(this.query)
        }
    }

    changePage(page: number) {
        this.query.values.page = page
        this.moveForSearch(this.query)
    }

    showAggregation(index: number) {
        this.aggregationIndex = index
        let modal = document.querySelector('.modal-content')
        disableBodyScroll(modal!)
    }

    hideAggregation() {
        this.aggregationIndex = null
        clearAllBodyScrollLocks()
    }

    beforeRouteUpdate(to: Route, from: Route, next: any) {
        this.executeSearch(to)
        next()
    }

    mounted() {
        this.executeSearch(this.$route)
        datasetStore.fetchHotTags({ reload: true })

        /*-- モーダルを表示した場合はこれを実行。 */
        // https://github.com/willmcpo/body-scroll-lock
        // let modal = document.querySelector('.modal-content')
        // disableBodyScroll(modal!)
        /*-- モーダルを解除した場合はこれを実行 */
        clearAllBodyScrollLocks()
    }

    created() {
    }
}
</script>

<style>
input[type=radio].agg-select {
    margin: 0px 2px 0px 2px;
}
input[type=radio].agg-select + label {
    margin-right: 5px;
}
</style>