<script setup lang="ts">
import type { TheoryArticle } from '~/types'
import { mainCategories, subCategories } from '~/utils/exams'
import { isApiEnabled } from '~/utils/api'
const { data, remove, deleteRemoteTheory } = useDatabase(),
  { isTeacher, requireTeacher } = useAuth(),
  { show } = useToast()
const main = ref('doc-hieu'),
  sub = ref('doc-hieu-tho'),
  editing = ref<TheoryArticle | null>(null),
  reading = ref<TheoryArticle | null>(null),
  deleting = ref<TheoryArticle | null>(null)
watch(main, (value) => (sub.value = subCategories[value]?.[0]?.id || ''))
const articles = computed(() => data.value.theory_articles.filter((t) => t.subCat === sub.value))
const mainItems = computed(() =>
  mainCategories.map((item) => ({
    ...item,
    count: data.value.theory_articles.filter((article) => article.mainCat === item.id).length,
  })),
)
const subItems = computed(() =>
  (subCategories[main.value] || []).map((item) => ({
    ...item,
    count: data.value.theory_articles.filter((article) => article.subCat === item.id).length,
  })),
)
function newArticle(): TheoryArticle {
  return { id: crypto.randomUUID(), title: '', mainCat: main.value, subCat: sub.value, type: 'reference', format: 'mixed', icon: '📚', desc: '', content: '', attachments: [] }
}
// The editor persists the post itself, including attachments.
function saved(article: TheoryArticle) {
  main.value = article.mainCat
  nextTick(() => (sub.value = article.subCat))
  editing.value = null
  show('Đăng bài thành công! 🌿')
}
async function destroy() {
  try {
    requireTeacher()
    if (deleting.value) {
      if (isApiEnabled()) await deleteRemoteTheory(deleting.value.id)
      else remove('theory_articles', deleting.value.id)
    }
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
      <button
        v-if="isTeacher"
        class="btn btn-primary"
        @click="editing = newArticle()"
      >
        ＋ Đăng bài viết
      </button>
    </div>
    <CategoryTabs v-model="main" :items="mainItems" />
    <CategoryTabs v-model="sub" :items="subItems" />
    <div class="grid">
      <TheoryCard
        v-for="article in articles"
        :key="article.id"
        :article="article"
        :teacher="isTeacher"
        @open="reading = article"
        @edit="editing = article"
        @remove="deleting = article"
      />
      <p v-if="!articles.length" class="empty-state">Chưa có bài viết nào.</p>
    </div>
    <TheoryReader v-if="reading" :article="reading" @close="reading = null" />
    <TheoryEditor
      v-if="editing && isTeacher"
      :category="main"
      :subcategory="sub"
      :article="editing.title ? editing : undefined"
      @saved="saved"
      @close="editing = null"
    />
    <ConfirmDialog
      v-if="deleting"
      message="Cô muốn xóa bài này?"
      @close="deleting = null"
      @confirm="destroy"
    />
  </section>
</template>
