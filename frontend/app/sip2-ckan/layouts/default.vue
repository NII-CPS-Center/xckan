<template>
    <div>
        <header>
            <div class="header__inner">
            <div class="header__logo">
                <a href="/">
                    <h1 class="level1-heading_logo"><span>データカタログ</span>横断検索システム</h1>
                </a>
            </div>
            <nav class="header__nav">
                <nuxt-link to="/about">利用方法について</nuxt-link>
                <nuxt-link to="/terms">利用規約</nuxt-link>
                <nuxt-link to="/api">API仕様書</nuxt-link>
            </nav>
            </div>
        </header>
            <nuxt />
        <footer>
            <div class="footer__inner">
            <div class="copyright">
                <small>copyright © SIP NIIコンソーシアム</small>
            </div>
            </div>
            <!-- /.footer__inner -->
        </footer>
    </div>
</template>

<script lang="ts">
import { Vue, Component } from 'nuxt-property-decorator'
import { datasetStore } from '~/store'
import { defaultQuery } from '~/store/dataset'

@Component({
})
export default class DefaultLayout extends Vue {
    keyword: string = ""

    get isStatic(): boolean {
        return ["/about", "/api", "/terms"].includes(this.$route.path)
    }

    search() {
        let query = defaultQuery()
        query.values.keyword = this.keyword

        this.$router.push({
            path: "/",
            query: query.toQuery(),
        })
    }

    mounted() {
    }
}
</script>

<style scoped>
.header__nav {
    flex: 0 0 300px;
    text-align: right;
}

.header__nav a {
    display: inline;
    padding: 5px 10px;
}
</style>