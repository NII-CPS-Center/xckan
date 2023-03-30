<template>
    <div>
      <div class="breadcrumb">
        <ol class="breadcrumb__list" itemscope itemtype="https://schema.org/BreadcrumbList">
        <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
            <a itemprop="item" href="/">
                <span itemprop="name">ホーム</span>
            </a>
            <meta itemprop="position" content="1" />
         </li>

          <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
              <span itemprop="name">ページが見つかりません</span>
            <meta itemprop="position" content="2" />
          </li>
        </ol>
      </div>

      <article class="content content-about">
        <main class="content__main content-about__main">
        <div class="content-about__head">
          <h1 class="level1-heading_detail">ページが見つかりません</h1>
         </div>
         <section class="content-about__item">
            <div class="content-about__item__inner content__error">
             <p>お探しのページは一時的にアクセスできない状況にあるか、移動もしくは削除された可能性があります。</p>
              <p>
                <a href="/" class="btn btn__medium">TOPページに戻る</a>
              </p>
            </div>
        </section>
        </main>
    </article>
    <!-- /.content -->

    </div>
</template>