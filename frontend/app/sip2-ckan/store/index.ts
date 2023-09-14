// index.tsを作成することで、Vuexストアが有効になる。
// https://ja.nuxtjs.org/guide/directory-structure

import { Store } from 'vuex'
import { initializeStores } from '~/utils/store-accessor'

const initializer = (store: Store<any>) => initializeStores(store)

export const plugins = [initializer]
export * from '~/utils/store-accessor'