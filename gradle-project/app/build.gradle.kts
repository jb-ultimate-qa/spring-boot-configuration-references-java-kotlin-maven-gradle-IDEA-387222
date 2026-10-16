plugins {
    java
    idea
    kotlin("jvm")
    kotlin("plugin.spring")
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
    testImplementation(kotlin("test"))
}
tasks.test { useJUnitPlatform() }
tasks.register<Test>("integrationTest") {
    testClassesDirs = integrationTest.output.classesDirs
    classpath = integrationTest.runtimeClasspath
    useJUnitPlatform()
}
