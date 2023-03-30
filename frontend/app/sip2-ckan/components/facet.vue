<template>
    <aside class="content__side">
      <section class="filter">
        <div class="filter__header">
            <h2 class="level2-heading_filter-head"><i class="fas fa-filter"></i>検索条件</h2>
            <a href="" class="filter__clear" @click.prevent.stop="$emit('clear-facet')">条件クリア ×</a>
        </div>
        <div class="filter__content filter__org">
          <div class="filter__content-head"><i class="fas fa-building"></i>組織</div>
            <ul class="filter__list">
                <li class="filter__item" :class="{ active: o[2] }" v-for="(o, i) in organizations" :key="i" v-show="i < 5 || collapses[0]">
                    <a v-if="o[2]" href="" @click.prevent.stop="$emit('remove-facet', 'organization', o[0])">{{ o[0] }}&nbsp;<span>({{ o[1] }})</span></a>
                    <a v-else href="" @click.prevent.stop="$emit('add-facet', 'organization', o[0])">{{ o[0] }}&nbsp;<span>({{ o[1] }})</span></a>
                </li>
            </ul>
            <p v-if="organizations.length > 0 && !organizations[0][2]" class="text-right">
                <a href="" class="viewall" @click.stop.prevent="toggleFacet(0)">
                    <span v-if="!collapses[0]">全て表示</span>
                    <span v-else>データが多い組織だけ表示する</span>
                </a>
            </p>
        </div>        
        <div class="filter__content filter__org">
          <div class="filter__content-head"><i class="fas fa-window-maximize"></i>サイト名</div>
            <ul class="filter__list">
                <li class="filter__item" :class="{ active: s[2] }" v-for="(s, i) in sites" :key="i" v-show="i < 5 || collapses[1]">
                    <a v-if="s[2]" href="" @click.prevent.stop="$emit('remove-facet', 'site', s[0])">{{ s[0] }}&nbsp;<span>({{ s[1] }})</span></a>
                    <a v-else href="" @click.prevent.stop="$emit('add-facet', 'site', s[0])">{{ s[0] }}&nbsp;<span>({{ s[1] }})</span></a>
                </li>
            </ul>
            <p v-if="sites.length > 0 && !sites[0][2]"  class="text-right">
                <a href="" class="viewall" @click.stop.prevent="toggleFacet(1)">
                    <span v-if="!collapses[1]">全て表示</span>
                    <span v-else>データが多いサイト名だけ表示する</span>
                </a>
            </p>
        </div>
        <div class="filter__content filter__tag">
          <div class="filter__content-head"><i class="fas fa-tag"></i>タグ<span>(複数選択可)</span></div>
            <ul class="filter__list">
                <li class="filter__item" :class="{ active: t[2] }" v-for="(t, i) in tags" :key="i" v-show="i < 5 || collapses[2]">
                    <a v-if="t[2]" href="" @click.prevent.stop="$emit('remove-facet', 'tag', t[0])">{{ t[0] }}&nbsp;<span>({{ t[1] }})</span></a>
                    <a v-else href="" @click.prevent.stop="$emit('add-facet', 'tag', t[0])">{{ t[0] }}&nbsp;<span>({{ t[1] }})</span></a>
                </li>
            </ul>
            <p class="text-right">
                <a href="" class="viewall" @click.stop.prevent="toggleFacet(2)">
                    <span v-if="!collapses[2]">全て表示</span>
                    <span v-else>多いタグだけ表示する</span>
                </a>
            </p>
        </div>
        <div class="filter__content filter__tag">
          <div class="filter__content-head"><i class="fas fa-file"></i>ファイル形式<span>(複数選択可)</span></div>
            <ul class="filter__list">
                <li class="filter__item" :class="{ active: f[2] }" v-for="(f, i) in formats" :key="i" v-show="i < 5 || collapses[3]">
                    <a v-if="f[2]" href="" @click.prevent.stop="$emit('remove-facet', 'format', f[0])">{{ f[0] }}&nbsp;<span>({{ f[1] }})</span></a>
                    <a v-else href="" @click.prevent.stop="$emit('add-facet', 'format', f[0])">{{ f[0] }}&nbsp;<span>({{ f[1] }})</span></a>
                </li>
            </ul>
            <p class="text-right">
                <a href="" class="viewall" @click.stop.prevent="toggleFacet(3)">
                    <span v-if="!collapses[3]">全て表示</span>
                    <span v-else>上位のファイル形式のみ表示する</span>
                </a>
            </p>
        </div>
      </section>
    </aside>
</template>

<script lang="ts">
import { Vue, Component, Prop } from 'nuxt-property-decorator'
import { Facet, facets, FacetKey } from '~/store/models'
import { datasetStore } from '~/store'

@Component
export default class FacetMenu extends Vue {
    @Prop({ type: Object, required: true })
    readonly facet!: Facet

    collapses: [boolean, boolean, boolean, boolean] = [false, false, false, false]

    get organizations(): [string, number, boolean][] {
        return this.sortFacets(facets(this.facet.organization), datasetStore.usedFacets.get("organization") ?? [], true)
    }

    get sites(): [string, number, boolean][] {
        return this.sortFacets(facets(this.facet.xckan_site_name), datasetStore.usedFacets.get("site") ?? [], true)
    }

    get tags(): [string, number, boolean][] {
        return this.sortFacets(facets(this.facet.tags), datasetStore.usedFacets.get("tag") ?? [], false)
    }

    get formats(): [string, number, boolean][] {
        return this.sortFacets(facets(this.facet.res_format), datasetStore.usedFacets.get("format") ?? [], false)
    }

    toggleFacet(index: number) {
        // タプルの要素更新ではビューに反映されない。代入しなおす。
        let collapses: [boolean, boolean, boolean, boolean] = [
            this.collapses[0],
            this.collapses[1],
            this.collapses[2],
            this.collapses[3],
        ]
        collapses[index] = !collapses[index]

        this.collapses = collapses
    }

    private sortFacets(facets: [string, number][], used: string[], onlySelected: boolean): [string, number, boolean][] {
        let acc: [Array<[string, number, boolean]>, Array<[string, number, boolean]>] = [[], []]

        acc = facets.reduce((a, v) => {
            if (used.includes(v[0]))  {
                a[0].push([v[0], v[1], true])
            } else {
                a[1].push([v[0], v[1], false])
            }
            return a
        }, acc)

        return (onlySelected && acc[0].length > 0) ? acc[0] : acc[0].concat(acc[1])
    }
}
</script>