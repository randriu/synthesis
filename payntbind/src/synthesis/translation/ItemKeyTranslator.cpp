#include "ItemKeyTranslator.h"

namespace synthesis {

    template<typename K>
    ItemKeyTranslator<K>::ItemKeyTranslator() : num_items(0) {
        // left intentionally blank
    }

    template<typename K>
    ItemKeyTranslator<K>::ItemKeyTranslator(uint64_t num_items) : num_items(num_items)  {
        item_key_to_translation.resize(num_items);
    }

    template<typename K>
    void ItemKeyTranslator<K>::clear() {
        item_key_to_translation.clear();
        translation_to_item_key.clear();
    }

    template<typename K>
    void ItemKeyTranslator<K>::resize(uint64_t num_items) {
        item_key_to_translation.resize(num_items);
    }

    template<typename K>
    uint64_t ItemKeyTranslator<K>::numTranslations() const {
        return translation_to_item_key.size();
    }

    template<typename K>
    bool ItemKeyTranslator<K>::hasTranslation(uint64_t item, K key) const {
        return item_key_to_translation[item].find(key) != item_key_to_translation[item].end();
    }

    template<typename K>
    uint64_t ItemKeyTranslator<K>::translate(uint64_t item, K key) {
        auto new_translation = numTranslations();
        auto const& result = item_key_to_translation[item].try_emplace(key,new_translation);
        if(result.second) {
            translation_to_item_key.push_back(std::make_pair(item,key));
        }
        return (*result.first).second;
    }

    template<typename K>
    std::pair<uint64_t,K> ItemKeyTranslator<K>::retrieve(uint64_t translation) const {
        return translation_to_item_key[translation];
    }

    template<typename K>
    std::vector<std::pair<uint64_t,K>> const& ItemKeyTranslator<K>::translationToItemKey() const {
        return translation_to_item_key;
    }

    template<typename K>
    std::vector<uint64_t> ItemKeyTranslator<K>::translationToItem() const {
        std::vector<uint64_t> translation_to_item(numTranslations());
        for(uint64_t translation = 0; translation<numTranslations(); translation++) {
            translation_to_item[translation] = translation_to_item_key[translation].first;
        }
        return translation_to_item;
    }

    template class ItemKeyTranslator<uint64_t>;
    template class ItemKeyTranslator<std::pair<uint64_t,uint64_t>>;
}