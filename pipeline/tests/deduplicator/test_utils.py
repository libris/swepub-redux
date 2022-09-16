from pipeline.util import compare_text, empty_string, split_title_subtitle_first_colon


def test_compare_text():
    assert compare_text(
        "This text are almost the same.", "This Text are almost the same", 0.9
    )
    assert compare_text(
        "This text are exactly the same.", "This text are exactly the same.", 1.0
    )
    assert not compare_text("This text are not at all the same.", "Hello world", 0.9)


def test_empty_string():
    assert empty_string(None)
    assert empty_string(" ")
    assert not empty_string("I am not an empty soul")


def test_split_title_subtitle_first_colon():
    maintitle, subtitle = split_title_subtitle_first_colon("No subtitle here")
    assert maintitle == "No subtitle here"
    assert subtitle is None

    maintitle, subtitle = split_title_subtitle_first_colon(
        "This is title:And this is subtitle"
    )
    assert maintitle == "This is title"
    assert subtitle == "And this is subtitle"

    maintitle, subtitle = split_title_subtitle_first_colon(
        "This is title:And this is subtitle with:extra colon"
    )
    assert maintitle == "This is title"
    assert subtitle == "And this is subtitle with:extra colon"
