<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    id: string
    label: string
    type?: string
    autocomplete?: string
    error?: string
    hint?: string
    required?: boolean
    /**
     * Text direction of the input content. Latin data such as email addresses and passwords
     * stays left to right even when the surrounding page is right to left.
     */
    dir?: 'ltr' | 'rtl' | 'auto'
  }>(),
  {
    type: 'text',
    required: false,
  },
)

const model = defineModel<string>({ required: true })

const describedBy = computed(() => {
  const ids: string[] = []
  if (props.hint && !props.error) {
    ids.push(`${props.id}-hint`)
  }
  if (props.error) {
    ids.push(`${props.id}-error`)
  }
  return ids.length > 0 ? ids.join(' ') : undefined
})
</script>

<template>
  <div class="field" :class="{ 'field--invalid': error }">
    <label :for="id">{{ label }}</label>
    <input
      :id="id"
      v-model="model"
      :type="type"
      :dir="dir"
      :autocomplete="autocomplete"
      :required="required"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="describedBy"
    />
    <p v-if="hint && !error" :id="`${id}-hint`" class="field-hint">{{ hint }}</p>
    <p v-if="error" :id="`${id}-error`" class="field-error">{{ error }}</p>
  </div>
</template>

<style scoped>
.field {
  display: grid;
  gap: var(--space-2);
}

label {
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: 700;
}

input {
  width: 100%;
  min-height: 2.9rem;
  padding: 0.7rem var(--space-3);
  color: var(--color-text);
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition:
    border-color 120ms ease,
    box-shadow 120ms ease;
}

input:hover {
  border-color: #cfb6c0;
}

input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgb(166 61 99 / 16%);
}

.field--invalid input {
  border-color: var(--color-danger);
}

.field--invalid input:focus {
  box-shadow: 0 0 0 3px rgb(179 38 30 / 14%);
}

.field-hint,
.field-error {
  margin: 0;
  font-size: var(--text-xs);
}

.field-hint {
  color: var(--color-text-muted);
}

.field-error {
  color: var(--color-danger);
  font-weight: 600;
}
</style>
