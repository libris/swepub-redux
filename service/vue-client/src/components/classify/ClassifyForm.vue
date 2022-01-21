<script>
import { mapGetters } from 'vuex';
import autoSize from 'autosize';
import VueSimpleSpinner from 'vue-simple-spinner';
import * as Network from '@/utils/Network';
import Helptexts from '@/assets/json/helptexts.json';

const HelpBubble = () => import('@/components/shared/HelpBubble');

export default {
  name: 'classify-form',
  components: {
    VueSimpleSpinner,
    HelpBubble,
  },
  data() {
    return {
      result: null,
      loading: false,
      input: {},
      levels: [
        { value: 3, label: '3-siffernivå', id: 'level_3' },
        { value: 5, label: '5-siffernivå', id: 'level_5' },
      ],
      pickedLevel: 3,
      errorMsg: '',
    };
  },
  methods: {
    getResult() {
      const msg = 'Ett fel har inträffat';
      this.errorMsg = '';
      this.result = null;
      this.loading = true;
      const jsonBody = this.inputAsJson();
      Network.post(`${this.settings.apiPath}/classify`, jsonBody)
        .then((response) => {
          this.loading = false;
          if (response.statusCode === 200) {
            this.result = response;
            this.$nextTick(() => this.highlightResult());
          } else {
            response.json().then((json) => {
              const reason = json.errors.join(', ');
              this.errorMsg = `${msg} : ${reason}`;
            })
              .catch(() => { // no json error
                this.errorMsg = `${msg}: ${response.status} ${response.statusText}`;
              });
          }
        })
        .catch((err) => {
          this.loading = false;
          this.errorMsg = `${msg}: ${err}`;
        });
    },
    highlightResult() {
      const resultContainer = this.$refs.result;
      resultContainer.scrollIntoView({ behavior: 'smooth' });
    },
    clear() {
      this.errorMsg = '';
      this.input = {};
      this.pickedLevel = 3;
      this.result = null;
      this.$nextTick(() => {
        autoSize.update(this.inputs);
        this.$refs.inputTitle.focus();
      });
    },
    inputAsJson() {
      const jsonAbstract = JSON.stringify({ level: this.pickedLevel, ...this.input });
      return jsonAbstract.replace(/\\n/g, ''); // remove newlines
    },
  },
  computed: {
    ...mapGetters([
      'settings',
    ]),
    classifyStatus() {
      return this.result.status;
    },
    suggestions() {
      return this.result.suggestions;
    },
    serviceDescr() {
      return Helptexts.classify.service_descr;
    },
    inputs() {
      return document.querySelectorAll('textarea');
    },
    language() {
      return this.settings.language;
    },
    canProceed() {
      return (!!this.input.abstract || !!this.input.keywords || !!this.input.title)
      && !this.loading;
    },
  },
  mounted() {
    this.$nextTick(() => {
      autoSize(this.inputs);
    });
  },
};
</script>

<template>
  <section class="Classify"
    id="classify-section"
    role="tabpanel"
    aria-labelledby="classify-tab">
    <p id="service-descr" v-html="serviceDescr"></p>
    <div class="Classify-form"
      role="form"
      aria-describedby="service-descr"
      :aria-busy="loading">
      <div class="Classify-formGroup">
        <label class="Classify-formLabel" for="title_input">Titel</label>
        <help-bubble bubbleKey="title"/>
        <textarea class="Classify-input"
          id="title_input"
          v-model="input.title"
          rows="1"
          ref="inputTitle"/>
      </div>
      <div class="Classify-formGroup">
        <label class="Classify-formLabel" for="abstract_input">Sammanfattning</label>
        <help-bubble bubbleKey="summary"/>
        <textarea id="abstract_input"
          name="abstract_input"
          class="Classify-input"
          v-model="input.abstract"
          rows="8"
          spellcheck="false"/>
      </div>
      <div class="Classify-formGroup">
        <label class="Classify-formLabel" for="keywords_input">Nyckelord</label>
        <help-bubble bubbleKey="keywords"/>
        <textarea class="Classify-input"
          id="keywords_input"
          v-model="input.keywords"
          rows="1"/>
      </div>
      <fieldset class="Classify-formGroup">
        <legend class="Classify-formLabel">Välj klassificeringsnivå</legend>
        <help-bubble bubbleKey="level"/>
        <div v-for="level in levels" :key="level.id">
          <input type="radio" :id="level.id" :value="level.value" v-model="pickedLevel">
          <label class="Classify-formLabel is-inline" :for="level.id">{{level.label}}</label>
        </div>
      </fieldset>
      <div class="Classify-controls">
        <button id="submit-btn"
          class="btn"
          @click.prevent="getResult"
          :class="{ 'disabled' : !canProceed }"
          :disabled="!canProceed">
          Visa</button>
        <button id="clear-btn"
          class="btn btn--warning"
          @click.prevent="clear"
          :class="{ 'disabled' : !canProceed }"
          :disabled="!canProceed">
          Rensa</button>
          <vue-simple-spinner v-if="loading"/>
        <div v-if="errorMsg">
          <p class="error" role="alert" aria-atomic="true">{{ errorMsg }}</p>
        </div>
      </div>
    </div>
    <transition name="fade">
      <section class="Classify-resultWrapper"
        v-show="result"
        aria-labelledby="result">
        <div class="Classify-resultLabel">
          <h2 id="result" class="heading heading-md">Resultat</h2>
          <help-bubble bubbleKey="result"/>
        </div>
        <div class="Classify-result"
          :class="{'Result' : result}"
          ref="result">
          <table v-if="result && result.status === 'match'"
            class="Result-table"
            cellspacing="0"
            cellpadding="0">
            <tr class="Result-row">
              <th class="Result-cell heading heading-xs">Kod</th>
              <th class="Result-cell heading heading-xs">Benämning</th>
              <th></th>
              <th class="Result-cell heading heading-xs">Värde</th>
            </tr>
            <tr v-for="(suggestion, index) in result.suggestions" :key="index" class="Result-row">
              <td class="Result-cell"
                v-if="suggestion[language] && suggestion[language].code">
                {{ suggestion[language].code }}</td>
              <td v-else></td>
              <td class="Result-cell"
                v-if="suggestion.swe && suggestion.swe.hasOwnProperty('prefLabel')">
                {{ suggestion.swe.prefLabel }}</td>
              <td v-else></td>
              <td class="Result-cell"
                v-if="suggestion.eng && suggestion.eng.hasOwnProperty('prefLabel')">
                {{ suggestion.eng.prefLabel }}</td>
              <td v-else></td>
              <td class="Result-cell" v-if="suggestion.hasOwnProperty('score')">
                {{ suggestion.score }}</td>
              <td v-else></td>
            </tr>
          </table>
          <p v-else-if="result && result.status === 'no match'" role="status">
            Ingen matchning
          </p>
        </div>
      </section>
    </transition>
  </section>
</template>

<style lang="scss">
.Classify {
  max-width: $screen-md;

  &-form {
    width: 100%;
    margin-top: 2em;
  }

  &-formGroup {
    padding: 0;
    margin-bottom: 1em;
  }

  &-formLabel {
  }

  &-input {
    resize: vertical;
    width: 100%;
  }

  &-serviceDescr {
    margin: 6rem 0;
    max-width: 768px;
  }

  &-controls {
    display: flex;
    align-items: center;
  }

  &-resultWrapper {
    margin-top: 2em;
  }

  &-resultLabel {
    display: flex;
    align-items: center;

    & * {
      margin-right: 5px;
    }
  }

  &-result {
    margin: 0;
    background-color: $white;
    border: 1px solid $mark;
    overflow: hidden;
    padding: 1em;
    max-width: 100%;
  }

  &-intro {
    flex: 1;
  }
}

.Result {
  display: flex;

  &-table {
    table-layout: fixed;
    word-break: break-all;
  }

  &-row {
    vertical-align: baseline;
  }

  &-cell {
    text-align: left;
    padding: 5px 20px 5px 5px;
    border-collapse: collapse;
    word-break: initial;
  }
}
</style>
