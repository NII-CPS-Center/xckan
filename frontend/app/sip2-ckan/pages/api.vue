<template>
    <div>
        <div class="head_border">
        </div>

        <article class="content content-about">
            <main class="content__main content-about__main">
                <div class="content-about__head">
                    <h1 class="level1-heading_detail">{{ page.title }}</h1>
                </div>
                <section class="content-about__item">
                    <div class="content-about__item__inner">
                        <nuxt-content :document="page" />
                    </div>
                </section>
            </main>
        </article>
    </div>
</template>

<script lang="ts">
import { Vue, Component } from 'nuxt-property-decorator'

@Component({
    async asyncData(context: any) {
        const page = await context.$content('api').fetch()
        return {page: page}
    },
})
export default class ApiPage extends Vue {
}

</script>