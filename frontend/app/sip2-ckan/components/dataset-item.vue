<template>
    <li class="result__item">
        <nuxt-link :to="{ name: 'datasets-id', params: { id: dataset.xckan_id } }"  class="result__link">
            <h3 class="level3-heading_result">{{ dataset.xckan_title }}</h3>
            <div v-if="hasImage" class="result__org-logo"><img :src="dataset.organization.image_url"></div>
            <div class="result__source">{{ dataset.xckan_site_name }}</div>
            <div class="result__description">{{ dataset.xckan_description.length < 512 ? dataset.xckan_description : dataset.xckan_description.substring(0, 512) + "..." }}
            </div>
            <div class="result__meta">
                <div class="result__date">最終更新日: {{ dataset.xckan_last_updated | df }}</div>
                <div class="result__file">
                    <i class="fas fa-file"></i> : {{ formats }}
                </div>
            </div>
        </nuxt-link>
        <div v-if="hasAggregation" class="aggregation"><a href="" class="btn-circle-3d" @click.prevent.stop="$emit('show-aggregation')">+</a></div>
    </li>
</template>

<script lang="ts">
import { Vue, Component, Prop } from 'nuxt-property-decorator'
import { Dataset } from '~/store/models'
import moment from 'moment'

@Component({
    filters: {
        df(s: string): string {
            return moment(s).format("YYYY/MM/DD HH:mm:ss")
        }
    }
})
export default class DatasetItem extends Vue {
    @Prop({ type: Object, required: true })
    readonly dataset!: Dataset

    @Prop({ default: false })
    readonly aggregation!: boolean

    get hasImage(): boolean {
        let url = this.dataset.organization?.image_url

        if (url) {
            return url.startsWith("http://") || url.startsWith("https://")
        } else {
            return false
        }
    }

    get hasAggregation(): boolean {
        return this.aggregation
    }

    get formats(): string {
        return this.dataset.resources.reduce((acc: Array<string>, r) => {
            if (r.format && !acc.includes(r.format!)) {
                acc.push(r.format!)
            }
            return acc
        }, []).join(", ")
    }
}
</script>