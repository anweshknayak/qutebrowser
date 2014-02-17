from PyQt5.QtCore import Qt, QModelIndex, QVariant, QPersistentModelIndex, QObject

class ModelTest(QObject):

    fetchingMore = False

    def __init__(self, model, parent=None):
        """Connect to all of the models signals.

        Whenever anything happens recheck everything.

        """
        super().__init__(parent)

        self.model = model

        model.columnsAboutToBeInserted.connect(self.runAllTests)
        model.columnsAboutToBeRemoved.connect(self.runAllTests)
        model.columnsInserted.connect(self.runAllTests)
        model.columnsRemoved.connect(self.runAllTests)
        model.dataChanged.connect(self.runAllTests)
        model.headerDataChanged.connect(self.runAllTests)
        model.layoutAboutToBeChanged.connect(self.runAllTests)
        model.layoutChanged.connect(self.runAllTests)
        model.modelReset.connect(self.runAllTests)
        model.rowsAboutToBeInserted.connect(self.runAllTests)
        model.rowsAboutToBeRemoved.connect(self.runAllTests)
        model.rowsInserted.connect(self.runAllTests)
        model.rowsRemoved.connect(self.runAllTests)

        # Special checks for changes
        model.layoutAboutToBeChanged.connect(self.layoutAboutToBeChanged)
        model.layoutChanged.connect(self.layoutChanged)

        #model.rowsAboutToBeInserted.connect(self.rowsAboutToBeInserted)
        #model.rowsAboutToBeRemoved.connect(self.rowsAboutToBeRemoved)
        #model.rowsInserted.connect(self.rowsInserted)
        #model.rowsRemoved.connect(self.rowsRemoved)
        model.dataChanged.connect(self.dataChanged)
        model.headerDataChanged.connect(self.headerDataChanged)

        self.runAllTests()

    def runAllTests(self):
        if self.fetchingMore:
            return
        self.nonDestructiveBasicTest()
        self.rowCount()
        self.columnCount()
        self.hasIndex()
        self.index()
        self.parent()
        self.data()

    def nonDestructiveBasicTest(self):
        """Tries to call a number of the basic functions (not all).

        ...to make sure the model doesn't outright segfault, testing the
        functions that makes sense.

        """
        assert self.model.buddy(QModelIndex()) == QModelIndex()
        self.model.canFetchMore(QModelIndex())
        assert self.model.columnCount(QModelIndex()) >= 0
        assert self.model.data(QModelIndex()) == QVariant()
        self.fetchingMore = True
        self.model.fetchMore(QModelIndex())
        self.fetchingMore = False
        flags = self.model.flags(QModelIndex())
        assert flags == Qt.ItemIsDropEnabled or flags == 0
        self.model.hasChildren(QModelIndex())
        self.model.hasIndex(0, 0)
        self.model.headerData(0, Qt.Horizontal)
        self.model.index(0, 0)
        self.model.itemData(QModelIndex())
        cache = QVariant()
        self.model.match(QModelIndex(), -1, cache)
        self.model.mimeTypes()
        assert self.model.parent(QModelIndex()) == QModelIndex()
        assert self.model.rowCount() >= 0
        variant = QVariant()
        self.model.setData(QModelIndex(), variant, -1)
        self.model.setHeaderData(-1, Qt.Horizontal, QVariant())
        self.model.setHeaderData(999999, Qt.Horizontal, QVariant())
        self.model.sibling(0, 0, QModelIndex())
        self.model.span(QModelIndex())
        self.model.supportedDropActions()

    def rowCount(self):
        """Test model's implementation of rowCount() and hasChildren().

        Models that are dynamically populated are not as fully tested here.
        """
    #     logging.debug("rc")
        # check top row
        topIndex = self.model.index(0, 0, QModelIndex())
        rows = self.model.rowCount(topIndex)
        assert rows >= 0
        if rows > 0:
            assert self.model.hasChildren(topIndex)

        secondLevelIndex = self.model.index(0, 0, topIndex)
        if secondLevelIndex.isValid():  # not the top level
            # check a row count where parent is valid
            rows = self.model.rowCount(secondLevelIndex)
            assert rows >= 0
            if rows > 0:
                assert self.model.hasChildren(secondLevelIndex)

        # The models rowCount() is tested more extensively in checkChildren(),
        # but this catches the big mistakes

    def columnCount(self):
        """Test model's implementation of columnCount() and hasChildren()."""
        # check top row
        topIndex = self.model.index(0, 0, QModelIndex())
        assert self.model.columnCount(topIndex) >= 0

        # check a column count where parent is valid
        childIndex = self.model.index(0, 0, topIndex)
        if childIndex.isValid():
            assert self.model.columnCount(childIndex) >= 0

        # columnCount() is tested more extensively in checkChildren(),
        # but this catches the big mistakes

    def hasIndex(self):
        """Test model's implementation of hasIndex()."""
    #     logging.debug("hi")
        # Make sure that invalid values returns an invalid index
        assert not self.model.hasIndex(-2, -2)
        assert not self.model.hasIndex(-2, 0)
        assert not self.model.hasIndex(0, -2)

        rows = self.model.rowCount()
        columns = self.model.columnCount()

        # check out of bounds
        assert not self.model.hasIndex(rows, columns)
        assert not self.model.hasIndex(rows + 1, columns + 1)

        if rows > 0:
            assert self.model.hasIndex(0, 0)

        # hasIndex() is tested more extensively in checkChildren(),
        # but this catches the big mistakes

    def index(self):
        """Test model's implementation of index()."""
    #     logging.debug("i")
        # Make sure that invalid values returns an invalid index
        assert self.model.index(-2, -2) == QModelIndex()
        assert self.model.index(-2, 0) == QModelIndex()
        assert self.model.index(0, -2) == QModelIndex()

        rows = self.model.rowCount()
        columns = self.model.columnCount()

        if rows == 0:
            return

        # Catch off by one errors
        assert self.model.index(rows, columns) == QModelIndex()
        assert self.model.index(0, 0).isValid()

        # Make sure that the same index is *always* returned
        a = self.model.index(0, 0)
        b = self.model.index(0, 0)
        assert a == b

        # index() is tested more extensively in checkChildren(),
        # but this catches the big mistakes

    def parent(self):
        """Test model's implementation of parent()."""
    #     logging.debug("p")
        # Make sure the model won't crash and will return an invalid QModelIndex
        # when asked for the parent of an invalid index.
        assert self.model.parent(QModelIndex()) == QModelIndex()

        if self.model.rowCount() == 0:
            return

        # Column 0                | Column 1    |
        # QModelIndex()           |             |
        #    \- topIndex          | topIndex1   |
        #         \- childIndex   | childIndex1 |

        # Common error test #1, make sure that a top level index has a parent
        # that is a invalid QModelIndex.
        topIndex = self.model.index(0, 0, QModelIndex())
        assert self.model.parent(topIndex) == QModelIndex()

        # Common error test #2, make sure that a second level index has a parent
        # that is the first level index.
        if self.model.rowCount(topIndex) > 0:
            childIndex = self.model.index(0, 0, topIndex)
            assert self.model.parent(childIndex) == topIndex

        # Common error test #3, the second column should NOT have the same children
        # as the first column in a row.
        # Usually the second column shouldn't have children.
        topIndex1 = self.model.index(0, 1, QModelIndex())
        if self.model.rowCount(topIndex1) > 0:
            childIndex = self.model.index(0, 0, topIndex)
            childIndex1 = self.model.index(0, 0, topIndex1)
            assert childIndex != childIndex1

        # Full test, walk n levels deep through the model making sure that all
        # parent's children correctly specify their parent.
        checkChildren(QModelIndex())


    def checkChildren(parent, currentDepth):
        """
        Called from the parent() test.

        A model that returns an index of parent X should also return X when asking
        for the parent of the index.

        This recursive function does pretty extensive testing on the whole model in an
        effort to catch edge cases.

        This function assumes that rowCount(), columnCount() and index() already work.
        If they have a bug it will point it out, but the above tests should have already
        found the basic bugs because it is easier to figure out the problem in
        those tests then this one.

        """
        # First just try walking back up the tree.
        p = parent
        while p.isValid():
            p = p.parent()

        # For models that are dynamically populated
        if self.model.canFetchMore(parent):
            self.fetchingMore = True
            self.model.fetchMore(parent)
            self.fetchingMore = False

        rows = self.model.rowCount(parent)
        columns = self.model.columnCount(parent)

        if rows > 0:
            assert self.model.hasChildren(parent)

        # Some further testing against rows(), columns(), and hasChildren()
        assert rows >= 0
        assert columns >= 0
        if rows > 0:
            assert self.model.hasChildren(parent)

        #logging('parent: {}, rows: {}, columns: {}, parent column: {}'.format(
        #    model.data(parent).value(), rows, columns, parent.column())

        topLeftChild = self.model.index(0, 0, parent)

        assert not self.model.hasIndex(rows + 1, 0, parent)
        for r in range(rows):
            if self.model.canFetchMore(parent):
                self.fetchingMore = True
                self.model.fetchMore(parent)
                self.fetchingMore = False
            assert not self.model.hasIndex(r, columns + 1, parent)
            for c in range(columns):
                assert self.model.hasIndex(r, c, parent)
                index = self.model.index(r, c, parent)
                # rowCount() and columnCount() said that it existed...
                assert index.isValid()

                # index() should always return the same index when called twice in a row
                modifiedIndex = self.model.index(r, c, parent)
                assert index == modifiedIndex

                # Make sure we get the same index if we request it twice in a row
                a = self.model.index(r, c, parent)
                b = self.model.index(r, c, parent)
                assert a == b

                sibling = self.model.sibling( r, c, topLeftChild)
                assert index == sibling

                sibling = topLeftChild.sibling( r, c)
                assert index == sibling

                # Some basic checking on the index that is returned
                assert index.self.model() == self.model
                assert index.row() == r
                assert index.column() == c
                # While you can technically return a QVariant usually this is a sign
                # of a bug in data().  Disable if this really is ok in your model.
    #            assert model.data(index, Qt.DisplayRole).isValid()

                # If the next test fails here is some somewhat useful debug you play with.

                if self.model.parent(index) != parent:
                    logging.debug(
                        'r: {}, c: {}, currentDepth: {}, data: {}, parent {}'.format(
                            r, c, currentDepth, self.model.data(index).value(),
                            self.model.data(parent).value()))
                    logging.debug('index: {}, parent: {}, model parent: {}'.format(
                            index, parent, self.model.parent(index)))
    #                 And a view that you can even use to show the model.
    #                 QTreeView view
    #                 view.setModel(self.model)
    #                 view.show()

                # Check that we can get back our real parent.
                assert self.model.parent(index) == parent

                # recursively go down the children
                if self.model.hasChildren(index) and currentDepth < 10:
                    #qDebug() << r << c << "has children" << self.model.rowCount(index)
                    #logging.debug("r {} / c {} has children {}".format(
                    #   r, c, self.model.rowCount(index)))
                    self.checkChildren(index, ++currentDepth)
                # elif currentDepth >= 10:
                #   logging.debug("checked 10 deep")

                # make sure that after testing the children that the index doesn't change.
                newerIndex = self.model.index(r, c, parent)
                assert index == newerIndex

    def data(self):
        """Tests model's implementation of data()"""
        # Invalid index should return an invalid qvariant
        assert not self.model.data(QModelIndex()).isValid()

        if self.model.rowCount() == 0:
            return

        # A valid index should have a valid QVariant data
        assert self.model.index(0, 0).isValid()

        # shouldn't be able to set data on an invalid index
        assert not self.model.setData(QModelIndex(), "foo", Qt.DisplayRole)

        # General Purpose roles that should return a QString
        variant = self.model.data(self.model.index(0, 0), Qt.ToolTipRole)
        if variant.isValid():
            assert variant.canConvert(QVariant.String)

        variant = self.model.data(self.model.index(0, 0), Qt.StatusTipRole)
        if variant.isValid():
            assert variant.canConvert(QVariant.String)

        variant = self.model.data(self.model.index(0, 0), Qt.WhatsThisRole)
        if variant.isValid():
            assert variant.canConvert(QVariant.String)


        # General Purpose roles that should return a QSize
        variant = self.model.data(self.model.index(0, 0), Qt.SizeHintRole)
        if variant.isValid():
            assert variant.canConvert(QVariant.Size)


        # General Purpose roles that should return a QFont
        fontVariant = self.model.data(self.model.index(0, 0), Qt.FontRole)
        if fontVariant.isValid():
            assert fontVariant.canConvert(QVariant.Font)


        # Check that the alignment is one we know about
        textAlignmentVariant = self.model.data(self.model.index(0, 0), Qt.TextAlignmentRole)
        if textAlignmentVariant.isValid():
            alignment = textAlignmentVariant.value()
            assert alignment == alignment & (Qt.AlignHorizontal_Mask | Qt.AlignVertical_Mask)


        # General Purpose roles that should return a QColor
        colorVariant = self.model.data(self.model.index(0, 0), Qt.BackgroundColorRole)
        if colorVariant.isValid():
            assert colorVariant.canConvert(QVariant.Color)


        colorVariant = self.model.data(self.model.index(0, 0), Qt.TextColorRole)
        if colorVariant.isValid():
            assert colorVariant.canConvert(QVariant.Color)


        # Check that the "check state" is one we know about.
        checkStateVariant = self.model.data(self.model.index(0, 0), Qt.CheckStateRole)
        if checkStateVariant.isValid():
            state = checkStateVariant.value()
            assert (state == Qt.Unchecked or
                    state == Qt.PartiallyChecked or
                    state == Qt.Checked)


    #def rowsAboutToBeInserted(parent, start, end):
    #    """Store what is about to be inserted to make sure it actually happens."""

    ##    logging.debug("rowsAboutToBeInserted start={} end={}, parent={}".format(
    ##       start, end, model.data(parent).value())
    ##    logging.debug("current count of parent={}, display of last={}".format(
    ##       self.model.rowCount(parent), self.model.data(self.model.index(start-1, 0, parent)))
    ##       self.model.index(start-1, 0, parent), self.model.data(
    ##       self.model.index(start-1, 0, parent)))
    #    # Changing c # FIXME
    #    c.parent = parent
    #    c.oldSize = self.model.rowCount(parent)
    #    c.last = self.model.data(self.model.index(start - 1, 0, parent))
    #    c.next = self.model.data(self.model.index(start, 0, parent))
    #    insert.push(c)


    #def rowsInserted(parent, start, end):
    #    """Confirm that what was said was going to happen actually did"""
    #    c = insert.pop()
    #    assert c.parent == parent
    ##    qDebug() << "rowsInserted"  << "start=" << start << "end=" << end << "oldsize=" << c.oldSize
    ##    << "parent=" << self.model.data(parent).value() << "current rowcount of parent=" << self.model.rowCount(parent)

    ##    for (int ii=start; ii <= end; ii++)
    ##   
    ##      qDebug() << "itemWasInserted:" << ii << self.model.data(self.model.index(ii, 0, parent))

    ##    qDebug()

    #    assert c.oldSize +(end - start + 1) == self.model.rowCount(parent)
    #    assert c.last == self.model.data(self.model.index(start - 1, 0, c.parent))

    #    if c.next != self.model.data(self.model.index(end + 1, 0, c.parent)):
    #        logging.debug('start={}, end={}'.format(start, end)
    #            for i in range(self.model.rowCount()):
    #                logging.debug('value={}'.format(sellf.model.index(i, 0).data().value()))

    #        logging.debug('next={}, data={}'.format(c.next, self.model.data(self.model.index(end + 1, 0, c.parent))))

    #    assert c.next == self.model.data(self.model.index(end + 1, 0, c.parent))


    def layoutAboutToBeChanged(self):
        for i in range(max(0, min(self.model.rowCount(), 100))):
            changing.append(QPersistentModelIndex(self.model.index(i, 0)))


    def layoutChanged(self):
        for i in range(changing.count()):
            p = changing[i]
            assert p == self.model.index(p.row(), p.column(), p.parent())

        changing.clear()


    #def rowsAboutToBeRemoved(parent, start, end):
    #    """Store what is about to be inserted to make sure it actually happens"""
    #    qDebug() << "ratbr" << parent << start << end
    #    Changing c
    #    c.parent = parent
    #    c.oldSize = self.model.rowCount(parent)
    #    c.last = self.model.data(self.model.index(start - 1, 0, parent))
    #    c.next = self.model.data(self.model.index(end + 1, 0, parent))
    #    remove.push(c)


    #def rowsRemoved(parent, start, end):
    #    """Confirm that what was said was going to happen actually did."""
    #    qDebug() << "rr" << parent << start << end
    #    Changing c = remove.pop()
    #    assert c.parent == parent
    #    assert c.oldSize -(end - start + 1) == self.model.rowCount(parent)
    #    assert c.last == self.model.data(self.model.index(start - 1, 0, c.parent))
    #    assert c.next == self.model.data(self.model.index(start, 0, c.parent))


    def dataChanged(topLeft, bottomRight):
        assert topLeft.isValid()
        assert bottomRight.isValid()
        commonParent = bottomRight.parent()
        assert topLeft.parent() == commonParent
        assert topLeft.row() <= bottomRight.row()
        assert topLeft.column() <= bottomRight.column()
        rowCount = self.model.rowCount(commonParent)
        columnCount = self.model.columnCount(commonParent)
        assert bottomRight.row() < rowCount
        assert bottomRight.column() < columnCount

    def headerDataChanged(orientation, start, end):
        assert start >= 0
        assert end >= 0
        assert start <= end
        itemCount = self.model.rowCount() if orientation == Qt.Vertical else self.model.columnCount()
        assert start < itemCount
        assert end < itemCount
