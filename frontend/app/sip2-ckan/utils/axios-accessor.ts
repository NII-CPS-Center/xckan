// https://typescript.nuxtjs.org/ja/cookbook/store.html#%E3%82%AF%E3%83%A9%E3%82%B9%E3%83%99%E3%83%BC%E3%82%B9
import { NuxtAxiosInstance } from '@nuxtjs/axios'
import { AxiosRequestConfig, AxiosResponse } from 'axios'
import { stringify } from 'querystring'

let $axios: NuxtAxiosInstance

function dumpRequest(config: AxiosRequestConfig) {
    const now = new Date()

    let text = `[Request to API]\n`
    text += `method: ${config.method}\n`
    text += `url: ${config.baseURL ?? ""}${config.url ?? ""}\n`
    text += `datetime: ${now} (${now.getTime()})\n`

    text += `headers:\n`
    for (let key in config.headers?.common) {
        text += `    ${key}: ${config.headers.common[key]}\n`
    }

    text += `queries:\n`
    for (let key in config.params) {
        text += `    ${key}: ${config.params[key]}\n`
    }

    return text
}

function dumpResponse(response: AxiosResponse) {
    const now = new Date()

    let text = `[Response from API]\n`
    text += `method: ${response.config.method ?? ""}\n`
    text += `url: ${response.config.baseURL ?? ""}${response.config.url ?? ""}\n`
    text += `datetime: ${now} (${now.getTime()})\n`

    text += `status: ${response.status} (${response.statusText})\n`

    text += `headers:\n`
    for (let key in response.headers) {
        text += `    ${key}: ${response.headers[key]}\n`
    }

    text += `body:\n`
    text += JSON.stringify(response.data)

    return text
}

export function initializeAxios(axios: NuxtAxiosInstance) {
    $axios = axios
    //$axios.setBaseURL('/api')
    $axios.defaults.paramsSerializer = params => stringify(params)

    if (process.env.apiLog) {
        $axios.interceptors.request.use(function(config) {
            console.log(dumpRequest(config))
            return config
        })

        $axios.interceptors.response.use(function(response) {
            console.log(dumpResponse(response))
            return response
        })
    }
}

export { $axios }