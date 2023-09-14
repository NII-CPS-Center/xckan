// https://github.com/championswimmer/vuex-module-decorators#accessing-modules-with-nuxtjs

import { Store } from 'vuex'
import { getModule } from 'vuex-module-decorators'
import DatasetStore from '~/store/dataset'

let datasetStore: DatasetStore

function initializeStores(store: Store<any>): void {
    datasetStore = getModule(DatasetStore, store)
}

export { initializeStores, datasetStore }