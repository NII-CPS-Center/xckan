// https://typescript.nuxtjs.org/ja/cookbook/store.html#%E3%82%AF%E3%83%A9%E3%82%B9%E3%83%99%E3%83%BC%E3%82%B9
import { Plugin } from '@nuxt/types'
import { initializeAxios } from '~/utils/axios-accessor'

const plugin: Plugin = ({ $axios, redirect }) => {
    initializeAxios($axios)
}

export default plugin