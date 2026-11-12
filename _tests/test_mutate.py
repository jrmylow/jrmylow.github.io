"""mutate.py: the check that each known bug in mutations.py fails the tests named for it."""

import textwrap
from pathlib import Path

import mutate
import pytest
from mutations import MUTATIONS

REPO = Path(__file__).resolve().parent.parent


def _mutation(old: str, new: str, tests: tuple[str, ...] = ("test_thing.py",)) -> mutate.Mutation:
    return mutate.Mutation("a bug", "thing.py", old, new, tests)


@pytest.fixture
def tiny_repo(tmp_path) -> Path:
    """A repo of one function and one test of it, with a comment the test cannot see."""
    (tmp_path / "thing.py").write_text("def double(n):\n    return n * 2  # twice n\n")
    (tmp_path / "test_thing.py").write_text(textwrap.dedent("""
            import pytest
            from thing import double

            def test_double():
                assert double(3) == 6

            @pytest.mark.skip(reason="always")
            def test_skipped():
                assert double(3) == 0
            """))
    return tmp_path


class TestApply:
    def test_replaces_the_one_occurrence(self, tiny_repo):
        mutate.apply(tiny_repo, _mutation("n * 2", "n * 3"))
        assert (tiny_repo / "thing.py").read_text() == "def double(n):\n    return n * 3  # twice n\n"

    def test_refuses_text_that_is_not_there(self, tiny_repo):
        """The source moved on, so the mutation no longer describes a bug in it."""
        with pytest.raises(mutate.StaleMutation, match="found 0 times"):
            mutate.apply(tiny_repo, _mutation("n * 4", "n * 3"))

    def test_refuses_text_that_occurs_twice(self, tiny_repo):
        """Which occurrence is the bug would be a guess."""
        (tiny_repo / "thing.py").write_text("limit = 3\nlimit = 3\n")
        with pytest.raises(mutate.StaleMutation, match="found 2 times"):
            mutate.apply(tiny_repo, _mutation("limit = 3", "limit = 4"))


class TestCheck:
    """check() runs a mutation's tests on a copy of the repo and says what they made of it."""

    def test_a_bug_the_tests_fail_on_is_caught(self, tiny_repo):
        result = mutate.check(_mutation("n * 2", "n * 3"), tiny_repo)
        assert (result.outcome, result.detail) == ("caught", "test_thing.py::test_double")

    def test_a_change_no_test_sees_survives(self, tiny_repo):
        result = mutate.check(_mutation("# twice n", "# thrice n"), tiny_repo)
        assert (result.outcome, result.detail) == ("survived", "1 test(s) passed")

    def test_a_change_that_stops_the_tests_running_is_broken(self, tiny_repo):
        """An import error fails every test, which says nothing about what the tests check."""
        assert mutate.check(_mutation("return n * 2", "return n *"), tiny_repo).outcome == "broken"

    def test_tests_that_all_skip_have_not_caught_it(self, tiny_repo):
        mutation = _mutation("n * 2", "n * 3", ("test_thing.py::test_skipped",))
        result = mutate.check(mutation, tiny_repo)
        assert (result.outcome, result.detail) == ("survived", "no named test ran")

    def test_the_repo_itself_is_left_alone(self, tiny_repo):
        before = (tiny_repo / "thing.py").read_text()
        mutate.check(_mutation("n * 2", "n * 3"), tiny_repo)
        assert (tiny_repo / "thing.py").read_text() == before
        assert sorted(path.name for path in tiny_repo.iterdir()) == ["test_thing.py", "thing.py"]


class TestMain:
    """The command fails unless every mutation it ran was caught."""

    @pytest.fixture
    def three(self, monkeypatch):
        """Three listed mutations whose outcome is their name's first word."""
        listed = [_mutation("a", "b") for _ in range(3)]
        names = ["caught tags one", "survived tags two", "caught cards three"]
        listed = [mutate.Mutation(name, m.path, m.old, m.new, m.tests) for name, m in zip(names, listed)]
        monkeypatch.setattr("mutations.MUTATIONS", listed)
        monkeypatch.setattr(mutate, "check", lambda mutation: mutate.Result(mutation.name.split()[0], "detail"))

    def test_fails_when_one_survives(self, three, capsys):
        assert mutate.main(["--jobs", "1"]) == 1
        assert "2 of 3 caught" in capsys.readouterr().out

    def test_passes_when_all_it_ran_were_caught(self, three, capsys):
        """Words pick mutations by name; the survivor's name has neither word."""
        assert mutate.main(["one", "cards"]) == 0
        assert "2 of 2 caught" in capsys.readouterr().out

    def test_matching_nothing_is_an_error_not_a_pass(self, three):
        assert mutate.main(["no-such-mutation"]) == 2


class TestMutationList:
    """The list stays true to the source without needing a build."""

    @pytest.mark.parametrize("mutation", MUTATIONS, ids=[m.name for m in MUTATIONS])
    def test_mutation_applies_to_the_source(self, mutation):
        assert (REPO / mutation.path).read_text(encoding="utf-8").count(mutation.old) == 1
        assert mutation.new != mutation.old

    @pytest.mark.parametrize("mutation", MUTATIONS, ids=[m.name for m in MUTATIONS])
    def test_named_tests_exist(self, mutation):
        assert mutation.tests, "a mutation with no tests can't be caught"
        for test in mutation.tests:
            assert (REPO / test.split("::")[0]).is_file(), f"{test} is not a test file"

    def test_names_are_unique(self):
        names = [mutation.name for mutation in MUTATIONS]
        assert len(names) == len(set(names))
