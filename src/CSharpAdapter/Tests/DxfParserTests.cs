using CSharpAdapter;
using Xunit;
public class DxfParserTests
{
    private static string Document(string body) => "0\nSECTION\n2\nENTITIES\n" + body + "0\nENDSEC\n0\nEOF\n";
    private static string Insert(string attributes) => "0\nINSERT\n2\nNK_STAMP\n8\nSTAMP\n" + attributes + "0\nSEQEND\n";
    private static string Attr(string tag, string value) => $"0\nATTRIB\n1\n{value}\n2\n{tag}\n8\nSTAMP\n";
    private static StampBlock ParseAttr(string tag, string value) => DxfParser.ParseText(Document(Insert(Attr(tag,value)))).Blocks.Single();
    // 12 shared fixture scenarios + 16 negative/semantic scenarios = 28 test cases.
    [Theory]
    [InlineData(1)][InlineData(2)][InlineData(3)][InlineData(4)][InlineData(5)][InlineData(6)]
    [InlineData(7)][InlineData(8)][InlineData(9)][InlineData(10)][InlineData(11)][InlineData(12)]
    public void SharedFixture(int n)
    {
        var result = DxfParser.ParseFile(Path.Combine(AppContext.BaseDirectory,"Samples",$"stamp_{n:00}.dxf"));
        var block = Assert.Single(result.Blocks);
        Assert.Equal(n.ToString(), block.Sheet); Assert.Equal("A4",block.Format);
        Assert.Equal($"NK-{n:000}-AR",block.Attributes["DESIGNATION"]);
        Assert.Equal($"Sheet {n:00}",block.Attributes["TITLE"]);
        Assert.Equal(new double[] {0,0,297,210},result.FrameBounds);
        Assert.Equal(4,result.Counts["ATTRIB"]); Assert.Contains("FRAME",result.Layers);
    }
    [Fact] public void EmptyRejected() => Assert.Throws<FormatException>(() => DxfParser.ParseText(""));
    [Fact] public void OddRejected() => Assert.Throws<FormatException>(() => DxfParser.ParseText("0\nSECTION\n2\n"));
    [Fact] public void BadCodeRejected() => Assert.Throws<FormatException>(() => DxfParser.ParseText("abc\nSECTION\n"));
    [Fact] public void HeaderCode9NotSheet() => Assert.Empty(DxfParser.ParseText("0\nSECTION\n2\nHEADER\n9\nSHEET1\n0\nENDSEC\n").Blocks);
    [Fact] public void SheetFromAttrib() => Assert.Equal("42",ParseAttr("SHEET","42").Sheet);
    [Fact] public void TitleFromAttrib() => Assert.Equal("Title",ParseAttr("TITLE","Title").Attributes["TITLE"]);
    [Fact] public void FormatFromAttrib() => Assert.Equal("A1",ParseAttr("FORMAT","A1").Format);
    [Fact] public void ExplicitMark() => Assert.Equal("АР",ParseAttr("MARK","АР").Mark);
    [Fact] public void MarkNotInferred() => Assert.Null(ParseAttr("DESIGNATION","NK-AR").Mark);
    [Fact] public void DuplicateRejected() => Assert.Throws<FormatException>(() => DxfParser.ParseText(Document(Insert(Attr("SHEET","1")+Attr("SHEET","2")))));
    [Fact] public void SeparateInserts() => Assert.Equal(new[]{"1","2"},DxfParser.ParseText(Document(Insert(Attr("SHEET","1"))+Insert(Attr("SHEET","2")))).Blocks.Select(b=>b.Sheet));
    [Fact] public void BoundsRead() => Assert.Equal(new double[]{-1,-2,3,4},DxfParser.ParseText(Document("0\nLWPOLYLINE\n10\n-1\n20\n-2\n10\n3\n20\n4\n")).FrameBounds);
    [Fact] public void LayersFromEntities() => Assert.Contains("FRAME",DxfParser.ParseText(Document("0\nLINE\n8\nFRAME\n")).Layers);
    [Fact] public void UnicodePreserved() => Assert.Equal("Общие данные",ParseAttr("TITLE","Общие данные").Attributes["TITLE"]);
    [Fact] public void MissingSheetNotInvented() => Assert.Null(ParseAttr("TITLE","T").Sheet);
    [Fact] public void TransformRejected() => Assert.Throws<NotSupportedException>(()=>DxfParser.ParseText(Document("0\nINSERT\n2\nNK\n50\n90\n")));
}
