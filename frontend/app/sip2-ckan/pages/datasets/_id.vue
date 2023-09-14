<template>
  <div v-if="dataset">
    <div class="head_border"></div>

    <article class="content content-detail">
      <div class="content-detail__meta">
        <div class="content-detail__meta__url">{{ dataset.xckan_id }}</div>
        <div class="content-detail__meta__update">
          {{ dataset.xckan_last_updated }}
        </div>
      </div>
      <main class="content__main content-detail__main">
        <div class="detail">
          <h1 class="level1-heading_detail">{{ dataset.xckan_title }}</h1>
          <a :href="siteUrl" class="content-detail__link" target="_blank">
            <span class="content-detail__link__source"
              >{{ dataset.xckan_site_url }} > dataset</span
            >
            <span class="content-detail__link__title"
              ><span v-if="dataset.xckan_site_name"
                >「{{ dataset.xckan_site_name }}」</span
              >に移動する​</span
            >
          </a>
          
          <section class="dataset__about">
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">データセットについて</h2>
            </div>
            <div class="dataset__description" v-html="_makeLink(dataset.xckan_description)"></div>
            <div class="dataset__about__footer">
              <div class="cc-icon" v-if="dataset.license_id">
                <template v-for="cc in creativeCommons">
                  <img :src="cc" />
                </template>
              </div>
              <ul
                class="tag"
                v-for="tag in dataset.tags"
                :key="tag.display_name"
              >
                <li class="tag__item">{{ tag.display_name }}</li>
              </ul>
            </div>
            <div class="update__meta" v-if="dataset.maintainer">
              <div class="update__user" v-if="dataset.maintainer">
                <span class="update__meta__title">更新者 :</span
                >{{ dataset.maintainer }}
              </div>
            </div>
          </section>

          <section class="dataset">
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">データセット</h2>
              <a
                :href="jsonDownlad"
                target="_blank"
                download="dataset.json"
                class="dataset__download"
                ><i class="fas fa-download"></i>JSONダウンロード</a
              >
            </div>
            <table class="dataset__table dataset__main">
              <tbody>
                <tr v-for="(value, key) in common" :key="key">
                  <th>{{ getTitle("", key) }}</th>
                    <td v-if="dataType(value) == 1" v-html="_makeLink(value)"></td>
                    <td v-else><img :src="value" /></td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="dataset" v-if="dataset.organization">
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">組織</h2>
            </div>
            <table class="dataset__table dataset__main">
              <tbody>
                <tr v-for="(value, key) in dataset.organization" :key="key">
                  <th>{{ getTitle("organization", key) }}</th>
                  <td v-html="_makeLink(value)"></td>
                </tr>
              </tbody>
            </table>
          </section>

          <section
            class="dataset"
            v-if="dataset.tags && dataset.tags.length > 0"
          >
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">データセットのキーワード</h2>
            </div>

            <div
              class="dataset__sub"
              v-for="(items, index) in dataset.tags"
              :key="index"
            >
              <h3 class="level3-heading_dataset">キーワード{{ index + 1 }}</h3>
              <table class="dataset__table dataset__main">
                <tbody>
                    <tr v-for="(value, key) in items" :key="key">
                      <th>{{ getTitle("tags", key) }}</th>
                      <td v-html="_makeLink(value)"></td>
                    </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section
            class="dataset"
            v-if="dataset.groups && dataset.groups.length > 0"
          >
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">グループ</h2>
            </div>

            <div
              class="dataset__sub"
              v-for="(items, index) in dataset.groups"
              :key="index"
            >
              <h3 class="level3-heading_dataset">グループ{{ index + 1 }}</h3>
              <table class="dataset__table dataset__main">
                <tbody>
                    <tr  v-for="(value, key) in items" :key="key">
                      <th>{{ getTitle("groups", key) }}</th>
                      <td v-html="_makeLink(value)"></td>
                    </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section
            class="dataset"
            v-if="dataset.resources && dataset.resources.length > 0"
          >
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">配信</h2>
            </div>

            <div
              class="dataset__sub"
              v-for="(items, index) in dataset.resources"
              :key="index"
            >
              <h3 class="level3-heading_dataset">配信{{ index + 1 }}</h3>
              <table class="dataset__table dataset__main">
                <tbody>
                    <tr v-for="(value, key) in items" :key="key">
                      <th>{{ getTitle("resource", key) }}</th>
                      <td v-html="_makeLink(value)"></td>
                    </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section
            class="dataset"
            v-if="dataset.extras && dataset.extras.length > 0"
          >
            <div class="dataset__head">
              <h2 class="level2-heading_dataset">付加情報</h2>
            </div>
            <table class="dataset__table dataset__main">
              <tbody>
                <tr v-for="(value, key) in extras" :key="key">
                  <th>{{ getTitle("extras", key) }}</th>
                  <td v-html="_makeLink(value)"></td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </main>
    </article>
    <!-- /.content -->
  </div>
</template>

<script lang="ts">
import { Vue, Component, PropSync, Provide } from "nuxt-property-decorator";
import { Context } from "@nuxt/types";
import { datasetStore } from "~/store";
import { DatasetTitles } from '~/data/dataset'
import { pathOf } from '~/utils/converter'

interface DisplayDataSetItem {
  title: String;
  parentKey: string;
  key: string;
}

interface DisplayItem {
  title: String;
  value: String;
}

interface DisplayTitle {
  key: String;
  title: String;
}

@Component
export default class DatasetPage extends Vue {
  private extras: { [key: string]: string } = {};
 
  get dataset(): any | null {
    let _dataset = datasetStore.of(pathOf(this.$route.params.id));
    if (_dataset) {
      if (Object.keys(this.extras).length == 0 && _dataset.extras) {
        _dataset.extras.forEach((element) => {
          if (element.value.length > 0) {
            this.extras[element.key] = element.value;
          }
        });
      }
    }
    return _dataset as any;
  }

  get common(): any | null {
    var _common = Object.assign({}, this.dataset);
    delete _common["groups"];
    delete _common["extras"];
    delete _common["organization"];
    delete _common["resources"];
    delete _common["tags"];
    return _common;
  }

  get siteUrl(): String {
    if (this.dataset) {
      return this.dataset.xckan_site_url;
    } else {
      return "";
    }
  }

  get notes(): String {
    if (this.dataset && this.dataset.notes) {
      return this._makeLink(this.dataset.notes);
    } else {
      return "";
    }
  }

  get jsonDownlad(): String {
    return process.env.api + "/package_show?id=" + this.$route.params.id;
  }

  get creativeCommons(): String[] {
    let licenseId = this.dataset.license_id.toLowerCase();
    var marks: String[] = [];
    if (licenseId.search("by") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/by.svg"));
    }
    if (licenseId.search("nc") >= 0) {
      if (licenseId.search("eu") >= 0) {
        marks.push(require("@/static/images/cc-icons-svg/nc-eu.svg"));
      } else if (licenseId.search("ja") >= 0) {
        marks.push(require("@/static/images/cc-icons-svg/nc-jp.svg"));
      } else {
        marks.push(require("@/static/images/cc-icons-svg/nc.svg"));
      }
    }
    if (licenseId.search("sa") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/sa.svg"));
    }
    if (licenseId.search("nd") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/nd.svg"));
    }
    if (licenseId.search("pd") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/pd.svg"));
    }
    if (licenseId.search("zero") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/zero.svg"));
    }
    if (licenseId.search("sampling") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/sampling.svg"));
    }
    if (licenseId.search("share") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/share.svg"));
    }
    if (licenseId.search("remix") >= 0) {
      marks.push(require("@/static/images/cc-icons-svg/remix.svg"));
    }
    if (marks.length > 0) {
      marks.unshift(require("@/static/images/cc-icons-svg/cc.svg"));
    }
    return marks;
  }

  isTruthy(data: any): Boolean {
    type Falsy = false | 0 | "" | null | undefined;
    const _isTruthy = <T>(x: T | Falsy): x is T => !!x;
    return _isTruthy(data);
  }

  isExistValue(dataItem: DisplayDataSetItem): Boolean {
    if (dataItem.parentKey.length > 0) {
      if (dataItem.parentKey == "extras") {
        return this.isTruthy(this.extras[dataItem.key]);
      }
      return (
        this.isTruthy(this.dataset[dataItem.parentKey]) &&
        this.isTruthy(this.dataset[dataItem.parentKey][dataItem.key])
      );
    } else {
      return this.isTruthy(this.dataset[dataItem.key]);
    }
  }

  getValue(dataItem: DisplayDataSetItem): any {
    if (dataItem.parentKey.length > 0) {
      if (dataItem.parentKey == "extras") {
        return this.extras[dataItem.key];
      }
      return this.dataset[dataItem.parentKey][dataItem.key];
    } else {
      if (dataItem.key == "tags") {
        let elements = this.dataset["tags"].map(
          (element: any) => element.display_name
        );
        return elements.join(", ");
      }
      return this.dataset[dataItem.key];
    }
  }

  isExistResourceValue(index: number, dataItem: DisplayDataSetItem): Boolean {
    if (dataItem.parentKey == "extras") {
      return this.isTruthy(this.extras[dataItem.key]);
    }
    return this.isTruthy(this.dataset.resources[index][dataItem.key]);
  }

  getResourceValue(index: number, dataItem: DisplayDataSetItem): any {
    if (dataItem.parentKey == "extras") {
      return this.isTruthy(this.extras[dataItem.key]);
    }
    return this.dataset.resources[index][dataItem.key];
  }

  get displayTitles(): { [key: string]: string } {
    return DatasetTitles
  }

  getTitle(prefix: string, key: string): string {
    var _key = key;
    if (prefix.length > 0) {
      _key = prefix + ":" + key;
    }

    return this.displayTitles[_key] ? this.displayTitles[_key] : key;
  }

  @Provide() headData: { [name: string]: any } = {};

  async asyncData(context: Context): Promise<any> {
    /*
    var pathOf = function(path: string): string {
        let match = path.match(/\.[^_]([^:]+):/)
        if(match) {
            let matchStr = path.substring(match.index!, match[0].length)
            path = path.replace(matchStr, matchStr.replace(/_/g, '__').replace(/____/g, '__'))
        }
        return path
    }
    */
    var path = pathOf(context.params.id);
    let data = await datasetStore.fetch({
      id: path,
    });
    console.log(data);

    if (!data) {
      return context.redirect("/404");
    }
    var head: { [name: string]: any } = {};
    head["title"] = data.xckan_title || "";
    head["description"] = data.xckan_description || data.notes || "(There is no description for this dataset.)";
    if (data.tags) {
      let keywords = data.tags.map((elem: any) => elem.display_name).join(",");
      head["keywords"] = keywords;
    }
    if (data.organization && data.organization.image_url) {
      head["image_url"] = data.organization.image_url;
    }
    if (data.organization && data.organization.title) {
      head["creator"] = data.organization.title;
    }
    head["identifier"] = data.xckan_id || null
    head["license"] = data.license_url ? data.license_url : (data.license ? data.license : null)
    head["url"] = data.xckan_site_url || null
    head["isOrganization"] = (data.organization && data.organization.type === 'organization')
    head["name"] = data.xckan_site_name || null

    return data ? { headData: head } : context.redirect("/404");
  }

  head() {
    var meta: { [name: string]: any }[] = [];
    meta.push({
      hid: "og:site_name",
      property: "og:site_name",
      content: "データカタログ横断検索システム",
    });
    meta.push({
      hid: "og:title",
      property: "og:title",
      content: this.headData["title"],
    });
    meta.push({
      hid: "twitter:title",
      property: "twitter:title",
      content: this.headData["title"],
    });
    let url = process.env.web + this.$route.path;
    meta.push({ hid: "og:url", property: "og:url", content: url });
    meta.push({
      hid: "twitter:card",
      property: "twitter:card",
      content: "summary",
    });
    if (this.headData["description"]) {
      meta.push({
        hid: "description",
        name: "description",
        content: this.headData["description"],
      });
      meta.push({
        hid: "og:description",
        property: "og:description",
        content: this.headData["description"],
      });
      meta.push({
        hid: "twitter:description",
        property: "twitter:description",
        content: this.headData["description"],
      });
    }
    if (this.headData["keywords"]) {
      meta.push({
        hid: "keywords",
        name: "keywords",
        content: this.headData["keywords"],
      });
    }
    if (this.headData["image_url"]) {
      meta.push({
        hid: "og:image",
        property: "og:image",
        content: this.headData["image_url"],
      });
    }
    if (this.headData["image_url"]) {
      meta.push({
        hid: "og:image",
        property: "og:image",
        content: this.headData["image_url"],
      });
      meta.push({
        hid: "twitter:image",
        property: "twitter:image",
        content: this.headData["image_url"],
      });
    }
    if (this.headData["creator"]) {
      meta.push({
        hid: "twitter:creator",
        property: "twitter:creator",
        content: this.headData["creator"],
      });
    }

    var jsonLD: { [name: string]: any } = {};
    jsonLD["@context"] = "https://schema.org/"
    jsonLD["@type"] = "Dataset"
    jsonLD["name"] = this.headData["title"]
    jsonLD["description"] = this.headData["description"]
    if(this.headData["isOrganization"] == "Organization") {
      jsonLD["creator"] = {
        "@type": "Organization",
        "name": this.headData["creator"]
      }
    } else {
      jsonLD["creator"] = {
        "@type": "Person",
        "name": this.headData["name"]
      }
    }
    jsonLD["alternateName"] = null
    jsonLD["citation"] = null
    jsonLD["hasPart"] = null
    jsonLD["isPartOf"] = null
    jsonLD["identifier"] = this.headData["identifier"]
    jsonLD["keywords"] = this.headData["keywords"]
    jsonLD["license"] = this.headData["license"]
    jsonLD["url"] = this.headData["url"]

    return {
      title: this.headData.title,
      meta: meta,
      __dangerouslyDisableSanitizers: ['script'],
      script: [{
          innerHTML: JSON.stringify(jsonLD, null, " "),
          type: 'application/ld+json'
        }]
    };
  }

  dataType(content: any): number {
    return (typeof content === 'string' && content.indexOf("data:image") >= 0) ? 0 : 1
  }

  convertString(content: any): any {
    var conv: any = content
    let self = this
    if(content == null || content === undefined) {
      return ""
    } else if(typeof content == 'object') {
      if(Array.isArray(content)) {
        var convArray = content.map(x => self.convertString(x))
        conv = convArray.join("<br/>")
      } else {
        var convArray = []
        Object.keys(content).forEach(key => {
          //console.log(key, content[key])
          convArray.push(key + ":" + self.convertString(content[key]))
        })
        conv = convArray.join("<br/>")
      }
    } 
    return conv
  }

  _makeLink(target: any): String {
    //var content = target
    var content = this.convertString(target)
    var regexp_url = /((h?)(ttps?:\/\/[a-zA-Z0-9.\-_@:/~?%&;=+#',()*!]+))/g; 
    var regexp_makeLink = function (
      all: String,
      url: String,
      h: String,
      href: String
    ) {
      return '<a href="h' + href + '">' + url + "</a>";
    };
    let _target = `${content}`;
    return _target.replace(regexp_url, regexp_makeLink);
  }
}
</script>