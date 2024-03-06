#pragma once

#include <cstdint>
#include <vector>

namespace synthesis {

    class ItemTranslator {
    public:

        /** Create empty translator. */
        ItemTranslator();
        /** Create translator of specified size. */
        ItemTranslator(uint64_t num_items);
        /** Remove all translations. */
        void clear();

        /** Number of created translations. */
        uint64_t numTranslations() const;
        /** Check if the item has a defined translation. */
        bool hasTranslation(uint64_t item) const;
        /** Translate an item. If the item does not have a translation, create and remember a new one. */
        uint64_t translate(uint64_t item);
        /** Retrieve the item that has the given translation. */
        uint64_t retrieve(uint64_t translation) const;
        
        /** Returns mapping of item to translation. */
        std::vector<uint64_t> const& itemToTranslation() const;
        /** Returns reverse mapping of translation to item. */
        std::vector<uint64_t> const& translationToItem() const;

    private:

        /** Maximum number of items to be translated. */
        uint64_t num_items;
        /**
         * For each item, contains a translation. Item without previously defined translation has translation equal to
         * \p num_items.
         */
        std::vector<uint64_t> item_to_translation;
        /** Reverse mapping of translation to item. Grows when new translations are created. */
        std::vector<uint64_t> translation_to_item;
    };

}