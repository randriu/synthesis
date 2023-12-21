#pragma once

#include <cstdint>
#include <map>
#include <utility>
#include <vector>

namespace synthesis {

    template<typename K>
    class ItemKeyTranslator {
    public:

        ItemKeyTranslator();
        ItemKeyTranslator(uint64_t num_items);
        void clear();
        void resize(uint64_t num_items);

        uint64_t numTranslations() const;

        /** Check if the item-key pair has a translation. */
        bool hasTranslation(uint64_t item, K key) const;
        
        /** Translate an item-key pair. If the pair does not have a translation, create and remember a new one. */
        uint64_t translate(uint64_t item, K key);
        
        /** Retrieve the item-key pair that has the given translation. */
        std::pair<uint64_t,K> retrieve(uint64_t translation) const;

        /** Retrieve the current translation-to-item-key mapping. */
        std::vector<std::pair<uint64_t,K>> const& translationToItemKey() const;

        /** Construct the current translation-to-item mapping. */
        std::vector<uint64_t> translationToItem() const;

    private:

        uint64_t num_items;
        
        std::vector<std::map<K,uint64_t>> item_key_to_translation;
        std::vector<std::pair<uint64_t,K>> translation_to_item_key;
    };

}