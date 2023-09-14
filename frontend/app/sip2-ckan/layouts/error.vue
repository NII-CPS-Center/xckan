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
              <span itemprop="name">エラーが発生しました</span>
            <meta itemprop="position" content="2" />
          </li>
        </ol>
      </div>

      <article class="content content-about">
        <main class="content__main content-about__main">
        <div class="content-about__head">
          <h1 class="level1-heading_detail">エラーが発生しました</h1>
         </div>
         <section class="content-about__item">
            <div class="content-about__item__inner content__error">
             <p>エラーが発生しました。しばらく経ってから再度アクセスしてください。</p>
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