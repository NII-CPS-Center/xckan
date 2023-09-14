import { createStore } from '~/.nuxt/store'
import { initializeStores, resourceStore } from '~/store'

describe("最初のテスト", () => {
    beforeEach(() => {
        initializeStores(createStore())
    })

    test("テスト", () => {
        expect(resourceStore.resources).toHaveLength(0)
    })
})