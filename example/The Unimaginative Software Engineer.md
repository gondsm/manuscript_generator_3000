This package supports manuscripts encoded in several ways (as you can see in the various importers), but the main format it supports are so-called index files.

An index file is simply a file that tells the tool what the sequence of files in your manuscript is, and where part/chapter breaks should live.

In this directory you will also find
- The files that compose this manuscript;
- An example [Markdown output](output/output.md).
- An example [PDF output](output/output.pdf)

Now let's use this as an index file for a little manuscript.

First comes a bit of config:

- [ ] -- Title: The Unimaginative Software Engineer
- [ ] -- Author: Gonçalo S. Martins

Config keys, as understood by the tool, are encoded in the `- [ ] -- key: value` format above. This means that every line that contains that sequence will be interpreted as some sort of configuration for the manuscript.

In a similar vein, the tool looks for part and chapter breaks in the following format:

- [ ] -- Chapter

So from this point onwards, the tool has introduced a chapter break in our manuscript.

Free floating text in index files is *not* converted into text in the manuscript. This means that you can freely take notes or add commentary around the definition of your manuscript, but at the same time this also means that there is no content in our manuscript so far!

Let's add some.

Content is added by including other files:

- [ ] [[010 - The Engineer Had a Problem]]

When the tool finds the line above, it will add it to the manuscript, so now our manuscript has a chapter and one entire file's worth of content. The content in that file can be formatted in any way Markdown can be, including *emphasis* and **bold**.

There is also no need for text in your manuscript definition. You can simply list out your chapters and files:

- [ ] -- Chapter
- [ ] [[020 - Huzzah, a solution!]]
- [ ] -- Chapter
- [ ] [[030 - A Flurry of Code]]

Chapters can contain more than one file, of course. The tool will automatically add scene breaks in chapters with multiple file. Similarly, files can also contain scene breaks in themselves; the markdown importer looks for these as a line containing only a `---`.