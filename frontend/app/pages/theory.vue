<script setup lang="ts">
import type { TheoryArticle } from '~/types'
import { mainCategories, subCategories } from '~/utils/exams'
const { data, upsert, remove } = useDatabase(),
  { isTeacher, requireTeacher } = useAuth(),
  { show } = useToast()
const main = ref('doc-hieu'),
  sub = ref('doc-hieu-tho'),
  editing = ref(false),
  reading = ref<TheoryArticle | null>(null),
  deleting = ref<TheoryArticle | null>(null)
watch(main, (value) => (sub.value = subCategories[value]?.[0]?.id || ''))
const articles = computed(() => data.value.theory_articles.filter((t) => t.subCat === sub.value))
function save(article: TheoryArticle) {
  try {
    requireTeacher()
    upsert('theory_articles', article)
    main.value = article.mainCat
    nextTick(() => (sub.value = article.subCat))
    editing.value = false
    show('Đăng bài thành công! 🌿')
  } catch (e) {
    show((e as Error).message)
  }
}
function destroy() {
  try {
    requireTeacher()
    if (deleting.value) remove('theory_articles', deleting.value.id)
    deleting.value = null
  } catch (e) {
    show((e as Error).message)
  }
}
</script>
<template>
  <section class="panel">
    <div class="flex justify-between items-center mb-3">
      <h2 class="section-title" style="margin: 0">🌿 Góc Kiến Thức</h2>
      <button v-if="isTeacher" class="btn btn-primary" @click="editing = true">
        ＋ Đăng bài viết
      </button>
    </div>
    <CategoryTabs v-model="main" :items="mainCategories" />
    <CategoryTabs v-model="sub" :items="subCategories[main] || []" />
    <div class="grid">
      <TheoryCard
        v-for="article in articles"
        :key="article.id"
        :article="article"
        :teacher="isTeacher"
        @open="reading = article"
        @remove="deleting = article"
      />
      <p v-if="!articles.length" class="empty-state">Chưa có bài viết nào.</p>
    </div>
    <TheoryReader v-if="reading" :article="reading" @close="reading = null" />
    <TheoryEditor
      v-if="editing && isTeacher"
      :category="main"
      :subcategory="sub"
      @save="save"
      @close="editing = false"
    />
    <ConfirmDialog
      v-if="deleting"
      message="Cô muốn xóa bài này?"
      @close="deleting = null"
      @confirm="destroy"
    />
  </section>
</template>
