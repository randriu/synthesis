import stormpy
import payntbind

from helpers.helper import get_stormpy_example_path, get_builder_options

class TestMiscellaneous:

    def test_get_matrix_rows(self):

        builder_5x5 = stormpy.SparseMatrixBuilder(5, 5, force_dimensions=False)

        builder_5x5.add_next_value(0, 0, 0)
        builder_5x5.add_next_value(0, 1, 0.1)
        builder_5x5.add_next_value(2, 2, 22)
        builder_5x5.add_next_value(2, 3, 23)


        builder_5x5.add_next_value(3, 2, 32)
        builder_5x5.add_next_value(3, 4, 34)
        builder_5x5.add_next_value(4, 3, 43)

        matrix_5x5 = builder_5x5.build()

        rows = payntbind.synthesis.get_matrix_rows(matrix_5x5, [1, 2, 3])
        
        assert len(rows) == 3
        assert len(rows[0]) == 0

        entry_one = False
        for entry in rows[1]:
            if entry_one:
                assert entry.column == 3
                assert entry.value() == 23.0
            else	:
                assert entry.column == 2
                assert entry.value() == 22.0
                entry_one = True
