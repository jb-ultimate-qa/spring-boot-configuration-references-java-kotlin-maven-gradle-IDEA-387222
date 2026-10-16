#!/usr/bin/env python3
"""Generate the IDEA-387222 test projects (temp.md, section 5).

Usage: python gen.py [ROOT]    ROOT defaults to the directory of this script.

Creates ROOT/gradle-project and ROOT/maven-project from temp.md section 5, and
ROOT/maven-single-module from the "How to check it" comment of the developer on
IDEA-387222 (2026-10-06). The Gradle wrapper is created separately with
`gradle wrapper`. If ROOT/IDEA-387222-TEST-CASES.md exists, it is copied into
every project root.
"""
import os, shutil, sys

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))

def write(project, path, text):
    full = os.path.join(root, project, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))

# Section 5.3: config files of both projects. Keys and markers must not change.
CONFIG = {
"app/src/main/resources/application.properties": r"""
# main config: TC-01 TC-02 TC-12
my.property=main
main.only.property=main-only
# TC-12: a placeholder inside the main config. The key exists only in the test config.
main.url=${test.only.property}/path
""",
"app/src/main/resources/application-dev.properties": r"""
my.property=main-dev
""",
"app/src/main/resources/application.yml": r"""
# main YAML: TC-03
yaml:
  property: main-yaml
  main-only: main-yaml-only
""",
"app/src/test/resources/application.properties": r"""
# test config: TC-04 TC-05 TC-13 TC-14
my.property=test
test.only.property=test-only
# TC-13: a placeholder inside the test config. The key exists only in the main config.
test.url=${main.only.property}/path
# TC-14: the import belongs to the test scope.
spring.config.import=classpath:extra-config.properties
""",
"app/src/test/resources/extra-config.properties": r"""
imported.test.property=imported
""",
"app/src/test/resources/application-test.properties": r"""
my.property=test-profile
""",
"app/src/test/resources/application.yml": r"""
# test YAML: TC-05Y NC-02
yaml:
  property: test-yaml
  test-only: test-yaml-only
""",
"app/src/test/resources/extra.properties": r"""
# XP-01
extra.key=from-test-extra
""",
"lib/src/test/resources/application.properties": r"""
# TC-09 NC-05
lib.test.only=lib-test
""",
}

# Section 5.4: Java sources of both projects.
JAVA = {
"app/src/main/java/demo/MainApplication.java": r"""
package demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class MainApplication {
  public static void main(String[] args) {
    SpringApplication.run(MainApplication.class, args);
  }
}
""",
"app/src/main/java/demo/MainService.java": r"""
package demo;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class MainService {
  @Value("${my.property}")                   // TC-01
  String myProperty;

  @Value("${main.only.property}")            // TC-02
  String mainOnly;

  @Value("${yaml.property}")                 // TC-03
  String yamlProperty;

  @Value("${test.only.property}")            // NC-01, XP-01 (fold)
  String testOnly;

  @Value("${yaml.test-only:none}")           // NC-02
  String yamlTestOnly;

  @Value("${imported.test.property:none}")   // NC-03
  String importedTestOnly;

  @Value("${extra.key:none}")                // XP-01
  String extraKey;

  @Value("${integration.only.property:none}") // XP-03
  String integrationOnly;
}
""",
"app/src/test/java/demo/MainServiceTest.java": r"""
package demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class MainServiceTest {
  @Value("${my.property}")                   // TC-04
  String myProperty;

  @Value("${test.only.property}")            // TC-05
  String testOnly;

  @Value("${yaml.test-only}")                // TC-05Y
  String yamlTestOnly;

  @Value("${imported.test.property}")        // TC-14
  String imported;

  @Value("${main.only.property}")            // TC-02T
  String mainOnly;

  @Test
  void runtimeTruth() {
    assertThat(myProperty).isEqualTo("test");
    assertThat(testOnly).isEqualTo("test-only");
    assertThat(yamlTestOnly).isEqualTo("test-yaml-only");
    assertThat(imported).isEqualTo("imported");
    assertThat(mainOnly).isEqualTo("main-only");
  }
}
""",
"app/src/test/java/demo/ProfiledTest.java": r"""
package demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
class ProfiledTest {
  @Value("${my.property}")                   // TC-06
  String myProperty;

  @Test
  void runtimeTruth() {
    assertThat(myProperty).isEqualTo("test-profile");
  }
}
""",
"app/src/test/java/demo/PropertiesAttributeTest.java": r"""
package demo;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "demo.injected=${test.only.property}")   // TC-07
class PropertiesAttributeTest {
  @Test
  void contextLoads() {
  }
}
""",
"lib/src/main/java/demo/lib/LibService.java": r"""
package demo.lib;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class LibService {
  @Value("${my.property}")                   // TC-08
  String myProperty;

  @Value("${test.only.property:none}")       // NC-04, XP-01 (fold)
  String appTestOnly;

  @Value("${lib.test.only:none}")            // NC-05
  String libTestOnly;
}
""",
"lib/src/test/java/demo/lib/LibServiceTest.java": r"""
package demo.lib;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;

class LibServiceTest {
  @Value("${lib.test.only}")                 // TC-09
  String libTestOnly;

  @Value("${test.only.property}")            // XP-02
  String appTestOnly;

  @Test
  void placeholder() {
  }
}
""",
}

# Gradle only: section 5.1, the integrationTest source set (5.3, 5.4) and Kotlin (5.5).
GRADLE = {
"settings.gradle.kts": r"""
rootProject.name = "idea-387222"
include("app", "lib")
""",
"build.gradle.kts": r"""
plugins {
    kotlin("jvm") version "2.2.20" apply false
}
subprojects {
    repositories { mavenCentral() }
}
""",
"gradle.properties": r"""
springBootVersion=4.0.0
""",
"lib/build.gradle.kts": r"""
plugins {
    `java-library`
    kotlin("jvm")
}
val springBootVersion: String by project
java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
kotlin { jvmToolchain(21) }
dependencies {
    api(platform("org.springframework.boot:spring-boot-dependencies:$springBootVersion"))
    api("org.springframework.boot:spring-boot-starter")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
tasks.test { useJUnitPlatform() }
""",
"app/build.gradle.kts": r"""
plugins {
    java
    idea
    kotlin("jvm")
}
val springBootVersion: String by project
java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
kotlin { jvmToolchain(21) }

// XP-03: a custom source set. The IDE import decides whether it is a test root.
val integrationTest: SourceSet by sourceSets.creating {
    compileClasspath += sourceSets.main.get().output
    runtimeClasspath += sourceSets.main.get().output
}
configurations["integrationTestImplementation"].extendsFrom(configurations.testImplementation.get())
configurations["integrationTestRuntimeOnly"].extendsFrom(configurations.testRuntimeOnly.get())

// XP-03b: uncomment, then reload the Gradle project. The IDE then marks the source set as tests.
// idea {
//     module {
//         testSources.from(integrationTest.java.srcDirs)
//         testResources.from(integrationTest.resources.srcDirs)
//     }
// }

dependencies {
    implementation(platform("org.springframework.boot:spring-boot-dependencies:$springBootVersion"))
    implementation(project(":lib"))
    implementation("org.springframework.boot:spring-boot-starter")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
tasks.test { useJUnitPlatform() }
tasks.register<Test>("integrationTest") {
    testClassesDirs = integrationTest.output.classesDirs
    classpath = integrationTest.runtimeClasspath
    useJUnitPlatform()
}
""",
"app/src/integrationTest/resources/application.properties": r"""
# XP-03
integration.only.property=it
""",
"app/src/integrationTest/java/demo/IntegrationSmokeTest.java": r"""
package demo;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class IntegrationSmokeTest {
  @Value("${integration.only.property}")     // XP-03
  String integrationOnly;

  @Test
  void contextLoads() {
  }
}
""",
"app/src/main/kotlin/demo/MainKotlinService.kt": r"""
package demo

import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service

@Service
class MainKotlinService {
  @Value("\${my.property}")                  // TC-01K
  lateinit var myProperty: String

  @Value("\${test.only.property}")           // NC-01K
  lateinit var testOnly: String
}
""",
"app/src/test/kotlin/demo/MainKotlinServiceTest.kt": r"""
package demo

import org.junit.jupiter.api.Test
import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.test.context.SpringBootTest

@SpringBootTest
class MainKotlinServiceTest {
  @Value("\${test.only.property}")           // TC-05K
  lateinit var testOnly: String

  @Test
  fun contextLoads() {
  }
}
""",
".gitignore": r"""
.gradle/
.kotlin/
build/
out/
.idea/
*.iml
""",
".gitattributes": r"""
/gradlew text eol=lf
*.bat text eol=crlf
*.jar binary
""",
}

# Maven only: section 5.2.
LIB_POM = r"""
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>4.0.0</version>
    <relativePath/>
  </parent>
  <groupId>demo</groupId>
  <artifactId>lib</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <properties><java.version>21</java.version></properties>
  <dependencies>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>
  </dependencies>
</project>
"""
APP_POM = LIB_POM.replace("<artifactId>lib</artifactId>", "<artifactId>app</artifactId>").replace(
    "  </dependencies>",
    "    <dependency><groupId>demo</groupId><artifactId>lib</artifactId><version>0.0.1-SNAPSHOT</version></dependency>\n"
    "  </dependencies>")
MAVEN = {
"pom.xml": r"""
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>demo</groupId>
  <artifactId>idea-387222</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <packaging>pom</packaging>
  <modules>
    <module>lib</module>
    <module>app</module>
  </modules>
</project>
""",
"lib/pom.xml": LIB_POM,
"app/pom.xml": APP_POM,
".gitignore": r"""
target/
.idea/
*.iml
""",
}

# The developer's check from YouTrack: "Single Maven module: foo=${my.key} in
# src/main/resources/application.properties should not resolve." The @Value lines
# repeat the Gradle part of the same comment in this layout.
SINGLE = {
"pom.xml": LIB_POM.replace("<artifactId>lib</artifactId>", "<artifactId>idea-387222-single</artifactId>"),
"src/main/resources/application.properties": r"""
# RL-01: my.key exists only in src/test/resources/application.properties.
foo=${my.key}
""",
"src/test/resources/application.properties": r"""
# test config: RL-01 RL-02 RL-03
my.key=test-value
""",
"src/main/java/demo/single/SingleApplication.java": r"""
package demo.single;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class SingleApplication {
  public static void main(String[] args) {
    SpringApplication.run(SingleApplication.class, args);
  }
}
""",
"src/main/java/demo/single/SingleService.java": r"""
package demo.single;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class SingleService {
  @Value("${my.key}")                        // RL-02
  String myKey;
}
""",
"src/test/java/demo/single/SingleServiceTest.java": r"""
package demo.single;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class SingleServiceTest {
  @Value("${my.key}")                        // RL-03
  String myKey;

  @Test
  void runtimeTruth() {
    assertThat(myKey).isEqualTo("test-value");
  }
}
""",
".gitignore": MAVEN[".gitignore"],
}

for path, text in {**CONFIG, **JAVA, **GRADLE}.items():
    write("gradle-project", path, text)
for path, text in {**CONFIG, **JAVA, **MAVEN}.items():
    write("maven-project", path, text)
for path, text in SINGLE.items():
    write("maven-single-module", path, text)

doc = os.path.join(root, "IDEA-387222-TEST-CASES.md")
if os.path.exists(doc):
    for project in ("gradle-project", "maven-project", "maven-single-module"):
        shutil.copyfile(doc, os.path.join(root, project, "IDEA-387222-TEST-CASES.md"))
print("generated in", root)
